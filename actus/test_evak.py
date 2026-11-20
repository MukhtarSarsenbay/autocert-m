from datetime import timedelta
from io import StringIO
from unittest.mock import Mock, patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .evak import EvakResponseError, fetch_evak_dates, parse_evak_dates, sync_evak_statuses
from .models import Actus


VIN = '5TDDK3EH7DS276996'


def result_html(registered='19.11.2026', called='-', vin=VIN):
    return (f'<div id="sp-component"><h4>VIN: {vin}</h4><h4>Device</h4>'
            f'<h4>Регистрация: {registered}</h4><h4>Прозвон: {called}</h4></div>')


class EvakParserTests(SimpleTestCase):
    def test_dates_and_missing_call(self):
        self.assertEqual(parse_evak_dates(result_html(), VIN), {'isRegistred': '19.11.2026'})
        self.assertEqual(parse_evak_dates(result_html(called='20.11.2026'), VIN),
                         {'isRegistred': '19.11.2026', 'isCalled': '20.11.2026'})

    def test_invalid_or_ambiguous_dates_are_not_saved(self):
        self.assertEqual(parse_evak_dates(result_html('31.02.2026', '01.11.2026 02.11.2026'), VIN), {})
        self.assertEqual(parse_evak_dates('<div id="sp-component">Не найдено</div>', VIN), {})

    def test_wrong_vin_and_changed_response_are_rejected(self):
        for html in ('<html>Service unavailable</html>', result_html(vin='1HGCM82633A004352')):
            with self.subTest(html=html), self.assertRaises(EvakResponseError):
                parse_evak_dates(html, VIN)

    def test_request_contract_and_http_errors(self):
        session = Mock()
        session.post.return_value.text = result_html()
        self.assertEqual(fetch_evak_dates(VIN.lower(), session), {'isRegistred': '19.11.2026'})
        self.assertEqual(session.post.call_args.kwargs['data'], {'query_reg': VIN})
        self.assertEqual(session.post.call_args.kwargs['timeout'], (5, 20))
        session.post.return_value.raise_for_status.side_effect = requests.HTTPError()
        with self.assertRaises(requests.HTTPError):
            fetch_evak_dates(VIN, session)


class EvakSyncTests(TestCase):
    def create_act(self, age=0, **fields):
        obj = Actus.objects.create(number=1, carVincode=fields.pop('carVincode', VIN), **fields)
        Actus.objects.filter(pk=obj.pk).update(createDate=timezone.now() - timedelta(days=age))
        return obj

    @patch('actus.evak.fetch_evak_dates')
    def test_registration_then_call_and_no_clearing_on_empty_result(self, fetch):
        obj = self.create_act(age=12)
        fetch.side_effect = [{'isRegistred': '19.11.2026'}, {}, {'isCalled': '20.11.2026'}]
        session = Mock()
        self.assertEqual(sync_evak_statuses(session=session)['updated'], 1)
        self.assertEqual(sync_evak_statuses(session=session)['updated'], 0)
        obj.refresh_from_db()
        self.assertEqual(obj.isRegistred, '19.11.2026')
        self.assertEqual(obj.isCalled, '-')
        self.assertEqual(sync_evak_statuses(session=session)['updated'], 1)
        obj.refresh_from_db()
        self.assertEqual(obj.isCalled, '20.11.2026')
        self.assertEqual(sync_evak_statuses(session=session)['skipped'], 1)
        self.assertEqual(fetch.call_count, 3)

    @patch('actus.evak.fetch_evak_dates', return_value={})
    def test_lookback_includes_29_days_excludes_31_and_future(self, fetch):
        recent = self.create_act(age=29)
        self.create_act(age=31, carVincode='1HGCM82633A004352')
        self.create_act(age=-1, carVincode='1HGCM82633A004353')
        session = Mock()
        self.assertEqual(sync_evak_statuses(session=session)['checked'], 1)
        fetch.assert_called_once_with(recent.carVincode, session)

    @patch('actus.evak.fetch_evak_dates')
    def test_failure_preserves_dates_and_continues_other_records(self, fetch):
        first = self.create_act(isRegistred='19.11.2026')
        second = self.create_act(carVincode='1HGCM82633A004352')
        fetch.side_effect = [requests.Timeout(), {'isRegistred': '20.11.2026'}]
        self.assertEqual(sync_evak_statuses(session=Mock()),
                         {'checked': 2, 'updated': 1, 'failed': 1, 'skipped': 0})
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.isRegistred, '19.11.2026')
        self.assertEqual(first.isCalled, '-')
        self.assertEqual(second.isRegistred, '20.11.2026')

    @patch('actus.evak.fetch_evak_dates')
    def test_concurrent_operator_edit_is_preserved(self, fetch):
        obj = self.create_act()
        def response(*args):
            Actus.objects.filter(pk=obj.pk).update(isRegistred='18.11.2026')
            return {'isRegistred': '19.11.2026'}
        fetch.side_effect = response
        self.assertEqual(sync_evak_statuses(session=Mock())['updated'], 0)
        obj.refresh_from_db()
        self.assertEqual(obj.isRegistred, '18.11.2026')


class EvakCommandTests(SimpleTestCase):
    @patch('actus.management.commands.sync_evak.sync_evak_statuses')
    def test_single_pass_reports_failures(self, sync):
        sync.return_value = {'checked': 1, 'updated': 0, 'failed': 1, 'skipped': 0}
        with self.assertRaises(CommandError):
            call_command('sync_evak', stdout=StringIO())
        sync.assert_called_once_with(days=30)

    @patch('actus.management.commands.sync_evak.signal.signal')
    @patch('actus.management.commands.sync_evak.time')
    @patch('actus.management.commands.sync_evak.Event')
    @patch('actus.management.commands.sync_evak.sync_evak_statuses')
    def test_loop_waits_until_next_five_minute_cycle_even_after_request_failure(self, sync, event, clock, signal):
        clock.monotonic.side_effect = [100, 105]
        sync.return_value = {'checked': 1, 'updated': 0, 'failed': 1, 'skipped': 0}
        event.return_value.is_set.side_effect = [False, True]
        call_command('sync_evak', loop=True, stdout=StringIO())
        sync.assert_called_once_with(days=30)
        event.return_value.wait.assert_called_once_with(295)

    def test_rejects_invalid_options(self):
        with self.assertRaises(CommandError):
            call_command('sync_evak', days=0, stdout=StringIO())
