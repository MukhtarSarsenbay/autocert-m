from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from testlog.services import get_or_create_testlog_creator


class Command(BaseCommand):
    help = "Ensure every active superuser has a SubUser for test log records."

    def handle(self, *args, **options):
        created_count = 0
        checked_count = 0

        for user in User.objects.filter(is_active=True, is_superuser=True).iterator():
            checked_count += 1
            _, created = get_or_create_testlog_creator(user)
            created_count += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"TestLog creators checked: {checked_count}; created: {created_count}."
            )
        )
