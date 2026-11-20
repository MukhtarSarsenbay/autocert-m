"""Compatibility entry point; scheduled deployments use the evak-sync service."""
import os
import django
from django.core.management import call_command

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'labauto.settings')
    django.setup()
    call_command('sync_evak')
