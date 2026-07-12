from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase

from subuser.models import SubUser

from .models import TestLog
from .services import get_or_create_testlog_creator


class MediaSettingsTests(SimpleTestCase):
    def test_media_url_is_absolute(self):
        self.assertEqual(settings.MEDIA_URL, "/media/")

    def test_health_endpoint(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok\n")


class TestLogCreatorTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )

    def test_creates_and_reuses_technical_subuser(self):
        creator, created = get_or_create_testlog_creator(self.superuser)

        self.assertTrue(created)
        self.assertEqual(creator.username, "admin_testlog")
        self.assertEqual(creator.creator, self.superuser)
        self.assertTrue(creator.is_active)
        self.assertFalse(creator.has_usable_password())

        same_creator, created = get_or_create_testlog_creator(self.superuser)
        self.assertFalse(created)
        self.assertEqual(same_creator, creator)

    def test_does_not_reactivate_disabled_subuser(self):
        disabled = SubUser.objects.create_user(
            username="disabled",
            password=None,
            creator=self.superuser,
            is_active=False,
            sign="",
        )

        creator, created = get_or_create_testlog_creator(self.superuser)

        disabled.refresh_from_db()
        self.assertTrue(created)
        self.assertNotEqual(creator, disabled)
        self.assertFalse(disabled.is_active)

    def test_avoids_username_collision_with_main_user(self):
        User.objects.create_user(username="admin_testlog", password="unused")

        creator, created = get_or_create_testlog_creator(self.superuser)

        self.assertTrue(created)
        self.assertEqual(creator.username, "admin_testlog_2")

    def test_management_command_creates_missing_creator(self):
        output = StringIO()

        call_command("ensure_testlog_creators", stdout=output)

        creator = SubUser.objects.get(creator=self.superuser, is_active=True)
        self.assertEqual(creator.username, "admin_testlog")
        self.assertIn("created: 1", output.getvalue())

    @patch("testlog.views._queue_pdf_render")
    def test_superuser_can_create_record_without_creator_id(self, queue_pdf_render):
        self.client.force_login(
            self.superuser,
            backend="django.contrib.auth.backends.ModelBackend",
        )

        response = self.client.post(
            "/app/testlog/form/?kind=default",
            {
                "temp_air": "20",
                "humidity": "50",
                "pressure": "100",
                "plate_height_up": "500",
                "vin_last4": "1HGCM82633A004352",
                "car_category": "M1",
                "test_number": "TEST-1",
            },
        )

        self.assertEqual(response.status_code, 202)
        record = TestLog.objects.get()
        self.assertEqual(record.creator.creator, self.superuser)
        self.assertEqual(record.creator.username, "admin_testlog")
        queue_pdf_render.assert_called_once_with(record)


class CsrfCookieTests(TestCase):
    def test_legacy_csrf_cookie_does_not_break_protected_post(self):
        client = Client(enforce_csrf_checks=True)
        client.cookies["csrftoken"] = "a" * 32

        csrf_page = client.get("/_test/csrf/")

        self.assertEqual(csrf_page.status_code, 200)
        self.assertNotEqual(settings.CSRF_COOKIE_NAME, "csrftoken")
        self.assertIn(settings.CSRF_COOKIE_NAME, csrf_page.cookies)
        csrf_token = csrf_page.content.decode()

        response = client.post(
            "/_test/csrf/",
            {"csrfmiddlewaretoken": csrf_token},
            secure=True,
            HTTP_ORIGIN="https://testserver",
        )

        self.assertEqual(response.status_code, 200)
