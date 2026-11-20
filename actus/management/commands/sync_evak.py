import signal
import time
from threading import Event

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from actus.evak import sync_evak_statuses


class Command(BaseCommand):
    help = 'Synchronize EVAK registration and call dates; --loop runs every 5 minutes.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true')
        parser.add_argument('--days', type=int, default=settings.EVAK_LOOKBACK_DAYS)
        parser.add_argument('--interval', type=int, default=settings.EVAK_SYNC_INTERVAL)

    def handle(self, *args, **options):
        if options['days'] < 1 or options['interval'] < 1:
            raise CommandError('--days and --interval must be positive')
        stop = Event()
        old_handlers = {}
        if options['loop']:
            for signum in (signal.SIGTERM, signal.SIGINT):
                old_handlers[signum] = signal.signal(signum, lambda *_: stop.set())
        try:
            while not stop.is_set():
                started = time.monotonic()
                close_old_connections()
                try:
                    result = sync_evak_statuses(days=options['days'])
                except Exception as exc:
                    # Infrastructure errors restart the dedicated Docker process.
                    raise CommandError(f'EVAK synchronization stopped: {type(exc).__name__}') from exc
                self.stdout.write('EVAK sync: ' + ', '.join(f'{key}={value}' for key, value in result.items()))
                self.stdout.flush()
                if not options['loop']:
                    if result['failed']:
                        raise CommandError('Some EVAK requests failed; existing dates were preserved')
                    return
                stop.wait(max(1, options['interval'] - (time.monotonic() - started)))
        finally:
            for signum, handler in old_handlers.items():
                signal.signal(signum, handler)
            close_old_connections()
