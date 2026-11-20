"""Read registration/call dates from EVAK without clearing previously known dates."""
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from .models import Actus

DATE_PATTERN = re.compile(r'\b\d{2}\.\d{2}\.\d{4}\b')


class EvakResponseError(Exception):
    pass


def valid_date(value):
    value = str(value or '').strip()
    if not DATE_PATTERN.fullmatch(value):
        return False
    try:
        datetime.strptime(value, '%d.%m.%Y')
    except ValueError:
        return False
    return True


def parse_evak_dates(html, vin):
    component = BeautifulSoup(html, 'html.parser').find('div', id='sp-component')
    if component is None:
        raise EvakResponseError('EVAK response has no result section')
    headings = [h.get_text(' ', strip=True) for h in component.find_all('h4')]
    # EVAK's legacy result contains VIN, device, registration and call headings.
    if len(headings) < 4:
        return {}
    returned_vins = re.findall(r'\b[A-HJ-NPR-Z0-9]{17}\b', ' '.join(headings[:2]).upper())
    if returned_vins and vin.strip().upper() not in returned_vins:
        raise EvakResponseError('EVAK returned a different VIN')
    result = {}
    for field, heading in zip(('isRegistred', 'isCalled'), headings[2:4]):
        dates = [d for d in DATE_PATTERN.findall(heading) if valid_date(d)]
        if len(dates) == 1:
            result[field] = dates[0]
    return result


def fetch_evak_dates(vin, session):
    response = session.post(
        settings.EVAK_STATUS_URL,
        data={'query_reg': vin.strip().upper()},
        timeout=(settings.EVAK_CONNECT_TIMEOUT, settings.EVAK_READ_TIMEOUT),
    )
    response.raise_for_status()
    return parse_evak_dates(response.text, vin)


def sync_evak_statuses(*, days=None, session=None, now=None):
    days = settings.EVAK_LOOKBACK_DAYS if days is None else days
    now = now or timezone.now()
    records = Actus.objects.filter(
        createDate__gte=now - timedelta(days=days), createDate__lte=now,
    ).only('id', 'carVincode', 'isRegistred', 'isCalled').order_by('id')
    counts = {'checked': 0, 'updated': 0, 'failed': 0, 'skipped': 0}
    owned_session = session is None
    session = session or requests.Session()
    try:
        for act in records.iterator(chunk_size=100):
            if valid_date(act.isCalled) and valid_date(act.isRegistred):
                counts['skipped'] += 1
                continue
            if not (act.carVincode or '').strip():
                counts['skipped'] += 1
                continue
            counts['checked'] += 1
            try:
                dates = fetch_evak_dates(act.carVincode, session)
            except (requests.RequestException, EvakResponseError):
                counts['failed'] += 1
                continue
            # Update only supplied dates. Empty results/outages never reset state.
            changed = False
            for field, value in dates.items():
                previous = getattr(act, field)
                if previous != value:
                    # A simultaneous operator edit takes precedence over this scan.
                    changed |= bool(Actus.objects.filter(pk=act.pk, **{field: previous}).update(**{field: value}))
            counts['updated'] += int(changed)
    finally:
        if owned_session:
            session.close()
    return counts
