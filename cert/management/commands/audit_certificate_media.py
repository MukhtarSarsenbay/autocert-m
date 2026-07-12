from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Q

from cert.models import Certificates


class Command(BaseCommand):
    help = "Check whether files referenced by a certificate exist in media storage."

    def add_arguments(self, parser):
        parser.add_argument("--sbkts", required=True)

    def handle(self, *args, **options):
        query = options["sbkts"].strip()
        certificates = Certificates.objects.filter(
            Q(sbkts__iexact=query) | Q(decision__icontains=query)
        ).order_by("id")

        if not certificates.exists():
            self.stdout.write(f"No certificate found for {query!r}.")
            return

        file_fields = [
            field
            for field in Certificates._meta.fields
            if isinstance(field, models.FileField)
        ]

        for certificate in certificates:
            self.stdout.write(
                f"Certificate id={certificate.pk} sbkts={certificate.sbkts!r}"
            )
            for field in file_fields:
                field_file = getattr(certificate, field.name)
                name = field_file.name or ""
                exists = bool(name) and field_file.storage.exists(name)
                self.stdout.write(
                    f"  {field.name}: name={name!r} exists={exists}"
                )

            expected_decision = f"decisions/Решение_{certificate.sbkts}.pdf"
            expected_exists = certificate.decision.storage.exists(expected_decision)
            self.stdout.write(
                f"  expected decision: name={expected_decision!r} "
                f"exists={expected_exists}"
            )
