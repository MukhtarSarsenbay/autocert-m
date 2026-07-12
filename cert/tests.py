from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import requests
from django.test import SimpleTestCase, override_settings

from cert.utils import convert_to


@override_settings(
    PDF_CONVERTER_URL="http://converter:3000",
    PDF_CONVERTER_TIMEOUT=12,
)
class PdfConversionTests(SimpleTestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.docx_path = Path(self.temporary_directory.name) / "document.docx"
        self.docx_path.write_bytes(b"docx payload")

    @patch("cert.utils.requests.post")
    def test_writes_pdf_atomically_from_converter_response(self, post):
        response = post.return_value.__enter__.return_value
        response.iter_content.return_value = [b"%PDF-1.7\n", b"content"]

        pdf_path = convert_to(self.docx_path)

        self.assertEqual(pdf_path, self.docx_path.with_suffix(".pdf"))
        self.assertEqual(pdf_path.read_bytes(), b"%PDF-1.7\ncontent")
        self.assertEqual(pdf_path.stat().st_mode & 0o777, 0o644)
        post.assert_called_once()
        _, kwargs = post.call_args
        self.assertEqual(
            post.call_args.args[0],
            "http://converter:3000/forms/libreoffice/convert",
        )
        self.assertEqual(kwargs["timeout"], (5, 12))
        self.assertEqual(kwargs["data"]["losslessImageCompression"], "true")
        self.assertEqual(kwargs["data"]["exportFormFields"], "false")

    @patch("cert.utils.requests.post")
    def test_rejects_non_pdf_response(self, post):
        response = post.return_value.__enter__.return_value
        response.iter_content.return_value = [b"not a PDF"]

        with self.assertRaisesRegex(OSError, "invalid response"):
            convert_to(self.docx_path)

        self.assertFalse(self.docx_path.with_suffix(".pdf").exists())
        self.assertEqual(
            list(self.docx_path.parent.glob(".document.pdf.*.tmp")),
            [],
        )

    @patch("cert.utils.requests.post")
    def test_wraps_converter_connection_error(self, post):
        post.side_effect = requests.ConnectionError("connection refused")

        with self.assertRaisesRegex(OSError, "converter request failed"):
            convert_to(self.docx_path)
