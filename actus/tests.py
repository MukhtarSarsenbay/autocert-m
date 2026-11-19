from pathlib import Path

from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from .admin import ActusAdminMenu
from .document_reader import (
    DocumentReaderResponseError,
    detect_document_content_type,
    recognize_document,
)


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

        self.assertIn("/api/actus/documents/recognize/${kind}/", script)
        self.assertNotIn("/dev/", script)




@override_settings(
    DOCUMENT_READER_ID_URL='https://reader.example/id',
    DOCUMENT_READER_VIN_URL='https://reader.example/vin',
    DOCUMENT_READER_CONNECT_TIMEOUT=5,
    DOCUMENT_READER_READ_TIMEOUT=60,
)
class DocumentReaderTests(SimpleTestCase):
    def test_multipart_upload_and_normalized_result(self):
        client = Mock()
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {'vin_code': 'TESTVIN', 'year': 2020, 'internal': 'ignore'}
        upload = SimpleUploadedFile('car.jpg', b'\xff\xd8\xffdata', content_type='application/octet-stream')
        upload.seek(2)
        self.assertEqual(detect_document_content_type(upload), 'image/jpeg')
        self.assertEqual(upload.tell(), 2)
        self.assertEqual(recognize_document('vin', upload, session=client), {'vin_code': 'TESTVIN', 'year': 2020})
        args, kwargs = client.post.call_args
        self.assertEqual(args, ('https://reader.example/vin',))
        self.assertEqual(kwargs['files']['file'], ('car.jpg', upload, 'image/jpeg'))
        self.assertEqual(upload.tell(), 0)
        self.assertEqual(kwargs['timeout'], (5, 60))

    def test_failure_and_invalid_responses_are_not_returned_as_success(self):
        for payload in ([], {}, {'error': 'internal error'}, {'flm': {'nested': 'bad'}}, {'flm': ' '}):
            with self.subTest(payload=payload):
                client = Mock()
                client.post.return_value.status_code = 200
                client.post.return_value.json.return_value = payload
                with self.assertRaises(DocumentReaderResponseError):
                    recognize_document('id', SimpleUploadedFile('id.pdf', b'%PDF-', content_type='application/pdf'), session=client)

    def test_timeout_does_not_disclose_service_details(self):
        client = Mock()
        client.post.side_effect = requests.Timeout('https://private.example/secret')
        with self.assertRaisesRegex(DocumentReaderResponseError, 'сейчас недоступен') as error:
            recognize_document('id', SimpleUploadedFile('id.pdf', b'%PDF-', content_type='application/pdf'), session=client)
        self.assertNotIn('private', str(error.exception))

    @override_settings(DOCUMENT_READER_ID_URL='')
    def test_missing_configuration(self):
        with self.assertRaisesRegex(DocumentReaderResponseError, 'не настроен'):
            recognize_document('id', SimpleUploadedFile('id.pdf', b'%PDF-'))


class RecognitionEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('reader-admin', is_staff=True)
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.force_login(self.user, backend='django.contrib.auth.backends.ModelBackend')
        token_response = self.client.get('/_test/csrf/')
        self.token = token_response.content.decode()

    def upload(self, kind='id', **extra):
        return self.client.post(
            f'/api/actus/documents/recognize/{kind}/',
            {'file': SimpleUploadedFile('id.pdf', b'%PDF-test', content_type='application/pdf')},
            format='multipart', **extra,
        )

    @patch('actus.views.recognize_document')
    def test_session_and_csrf_upload(self, reader):
        def recognize(kind, upload):
            self.assertEqual(upload.read(), b'%PDF-test')
            return {'flm': 'Test Person', 'uid': '123456789012'}
        reader.side_effect = recognize
        response = self.upload(HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['flm'], 'Test Person')
        self.assertEqual(reader.call_args.args[0], 'id')

    @patch('actus.views.recognize_document')
    def test_missing_csrf_and_anonymous_are_rejected(self, reader):
        self.assertEqual(self.upload().status_code, 403)
        self.client.logout()
        self.assertEqual(self.upload().status_code, 403)
        reader.assert_not_called()

    @patch('actus.views.recognize_document')
    def test_invalid_uploads_do_not_reach_service(self, reader):
        headers = {'HTTP_X_CSRFTOKEN': self.token}
        self.assertEqual(self.upload(kind='unknown', **headers).status_code, 404)
        url = '/api/actus/documents/recognize/id/'
        self.assertEqual(self.client.post(url, {}, **headers).status_code, 400)
        self.assertEqual(self.client.post(url, {'file': SimpleUploadedFile('bad.txt', b'hello')}, **headers).status_code, 400)
        with override_settings(DOCUMENT_READER_MAX_FILE_SIZE=2):
            self.assertEqual(self.upload(**headers).status_code, 400)
        reader.assert_not_called()

    @patch('actus.views.recognize_document', side_effect=DocumentReaderResponseError('Сервис недоступен'))
    def test_upstream_error(self, reader):
        response = self.upload(HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data['error'], 'Сервис недоступен')


class ActSupplierDocumentTests(TestCase):
    def generate_documents(self, username, with_stale_profile):
        from datetime import date
        from shutil import copytree
        from tempfile import TemporaryDirectory
        from zipfile import ZipFile
        from lxml import etree
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from subuser.models import Profile, SubUser
        from .models import Actus, Button
        from .company import SUPPLIER_CONTEXT, DIRECTOR_FULL_NAME, DIRECTOR_GENITIVE

        user = User.objects.create_user(username, is_staff=True, is_superuser=True)
        employee = SubUser.objects.create_user('act-employee', creator=user, sign='')
        if with_stale_profile:
            Profile.objects.create(user=user, vendor='OLD COMPANY', uid='OLD BIN', iik='OLD IBAN', bik='OLD BIC')
        button = Button.objects.create(iccid='89997090000000000000', hwname='FALCON', user=employee)
        obj = Actus(number=1, button=button, frln='Test Customer', personUid='111111111111',
                    personNumber='000000001', personPublic=date(2025, 1, 1), address='Customer address',
                    carVincode='5TDDK3EH7DS276996', carMarka='TOYOTA', carYear='2013')
        request = RequestFactory().get('/')
        request.user = user
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            copytree(BASE_DIR / 'media/ref', root / 'media/ref')
            def convert(source):
                target = Path(source).with_suffix('.pdf')
                target.write_bytes(b'%PDF-test')
                return target
            with override_settings(MEDIA_ROOT=root / 'media'), patch('actus.admin.BASE_DIR', root), patch('actus.admin.convert_to', side_effect=convert):
                ActusAdminMenu(Actus, AdminSite()).save_model(request, obj, None, False)
                obj.refresh_from_db()
                self.assertTrue(obj.isClose)
                for field in (obj.act, obj.contract):
                    with ZipFile(Path(field.path).with_suffix('.docx')) as z:
                        document = etree.fromstring(z.read('word/document.xml'))
                        text = ''.join(document.xpath('//*[local-name()="t"]/text()'))
                        images = [z.read(name) for name in z.namelist() if name.startswith('word/media/')]
                        if field == obj.act:
                            for key, value in SUPPLIER_CONTEXT.items():
                                if key != 'vendor_frln':
                                    self.assertIn(value, text, key)
                            self.assertIn(DIRECTOR_GENITIVE, text)
                            self.assertNotIn('OLD ', text)
                            self.assertTrue((BASE_DIR / 'media/ref/act_executor_medeu.png').read_bytes() in images, 'Missing combined executor image')
                            descriptions = document.xpath('//*[local-name()="docPr"]/@descr')
                            self.assertTrue(any(DIRECTOR_FULL_NAME in value for value in descriptions))
                            self.assertEqual(len(document.xpath('//*[local-name()="drawing"]')), 1)
                        else:
                            self.assertIn(DIRECTOR_FULL_NAME, text)
                            self.assertIn(DIRECTOR_GENITIVE, text)
                            self.assertNotIn('Сайдхакимов', text)
                            self.assertFalse((BASE_DIR / 'media/ref/act_executor_medeu.png').read_bytes() in images, 'Act image must not appear in contracts')
                    if field == obj.act or username != 'qaztehna':
                        self.assertIn('Test Customer', text)
                        self.assertIn('111111111111', text)
                    else:
                        self.assertIn('190840008556', text)
                        self.assertIn('KZ2294804KZT22031696', text)

    def test_empty_administrator_profile_uses_company_requisites(self):
        self.generate_documents('another-admin', False)

    def test_qaz_contract_keeps_customer_and_uses_company_director(self):
        self.generate_documents('qaztehna', True)
