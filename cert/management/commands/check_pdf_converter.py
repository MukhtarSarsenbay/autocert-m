from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from django.core.management.base import BaseCommand, CommandError
from docx import Document

from cert.utils import convert_to


class Command(BaseCommand):
    help = "Run a real DOCX to PDF conversion through the configured service."

    def handle(self, *args, **options):
        with TemporaryDirectory() as directory:
            docx_path = Path(directory) / "converter-check.docx"
            document = Document()
            document.add_paragraph("PDF converter check: АБВ ӘІҢҒҮҰҚӨҺ")
            document.save(docx_path)

            started_at = monotonic()
            try:
                pdf_path = convert_to(docx_path)
            except (OSError, FileNotFoundError) as exc:
                raise CommandError(str(exc)) from exc

            if not pdf_path.is_file() or not pdf_path.read_bytes().startswith(b"%PDF-"):
                raise CommandError("PDF converter did not create a valid PDF")

            elapsed = monotonic() - started_at
            self.stdout.write(self.style.SUCCESS(f"PDF converter OK ({elapsed:.2f}s)"))
