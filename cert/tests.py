from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase, override_settings
from docxtpl import DocxTemplate

from cert.utils import convert_to
from cert.services import resolve_certificate_creator
from subuser.models import SubUser


BASE_DIR = Path(__file__).resolve().parent.parent


class SignatureTemplateCompatibilityTests(SimpleTestCase):
    def test_dynamic_signature_placeholders_are_available(self):
        cases = (
            ("application.docx", "sigtest1.png"),
            ("contract.docx", "sign.png"),
            ("logbook.docx", "sign.png"),
            ("conclusion.docx", "sing.png"),
            ("protocol_b.docx", "sign.png"),
            ("protocol_o.docx", "sign.png"),
        )

        with TemporaryDirectory() as temporary_directory:
            for index, (template_name, placeholder) in enumerate(cases):
                with self.subTest(template=template_name, placeholder=placeholder):
                    template = DocxTemplate(BASE_DIR / "media" / "ref" / template_name)
                    template.replace_pic(placeholder, BASE_DIR / "sign.png")
                    template.render({})
                    template.save(Path(temporary_directory) / f"{index}.docx")

    def test_technical_expert_templates_render_with_fixed_signatures(self):
        with TemporaryDirectory() as temporary_directory:
            for template_name in ("tex_expert.docx", "tex_expert_p.docx"):
                with self.subTest(template=template_name):
                    template = DocxTemplate(BASE_DIR / "media" / "ref" / template_name)
                    template.render({})
                    template.save(Path(temporary_directory) / template_name)


class CertificateCreatorResolutionTests(SimpleTestCase):
    def test_keeps_existing_creator(self):
        existing_creator = object()
        certificate = MagicMock(creator_id=17, creator=existing_creator)

        creator = resolve_certificate_creator(certificate, object())

        self.assertIs(creator, existing_creator)
        certificate.save.assert_not_called()

    def test_assigns_current_subuser_to_legacy_certificate(self):
        certificate = MagicMock(creator_id=None)
        request_user = SubUser(username="employee")

        creator = resolve_certificate_creator(certificate, request_user)

        self.assertIs(creator, request_user)
        self.assertIs(certificate.creator, request_user)
        certificate.save.assert_called_once_with(update_fields=["creator"])

    def test_does_not_guess_creator_for_company_account(self):
        certificate = MagicMock(creator_id=None)

        creator = resolve_certificate_creator(certificate, object())

        self.assertIsNone(creator)
        certificate.save.assert_not_called()


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
