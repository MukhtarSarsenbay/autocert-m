from pathlib import Path

from django.test import SimpleTestCase

from .admin import ActusAdminMenu


BASE_DIR = Path(__file__).resolve().parent.parent


class ActusDocumentRecognitionScriptTests(SimpleTestCase):
    def test_uses_django_admin_jquery_namespace(self):
        script = (BASE_DIR / "static" / "js" / "custom_list_color.js").read_text()

        self.assertTrue(script.startswith("(function($) {"))
        self.assertTrue(script.rstrip().endswith("})(django.jQuery);"))
        self.assertNotIn("if (!$)", script)

    def test_does_not_load_a_second_jquery(self):
        scripts = ActusAdminMenu.Media.js

        self.assertNotIn("ajax.googleapis.com", " ".join(scripts))
        self.assertLess(
            scripts.index("admin/js/jquery.init.js"),
            scripts.index("js/custom_list_color.js"),
        )

    def test_recognition_endpoints_remain_wired(self):
        script = (BASE_DIR / "static" / "js" / "custom_list_color.js").read_text()

        self.assertIn("/detectID/", script)
        self.assertIn("/detectVIN/", script)
