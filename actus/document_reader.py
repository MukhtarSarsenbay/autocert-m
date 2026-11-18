"""Forward uploaded act documents to the configured recognition service."""
import requests
from django.conf import settings

DOCUMENT_READER_SETTINGS = {
    "id": "DOCUMENT_READER_ID_URL",
    "vin": "DOCUMENT_READER_VIN_URL",
}
CONTENT_TYPES = {
    "application/pdf": "application/pdf", "application/x-pdf": "application/pdf",
    "image/jpeg": "image/jpeg", "image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg",
}


class DocumentReaderResponseError(Exception):
    pass


def detect_document_content_type(uploaded_file):
    reported = (getattr(uploaded_file, "content_type", "") or "").partition(";")[0].strip().lower()
    if reported in CONTENT_TYPES:
        return CONTENT_TYPES[reported]
    position = uploaded_file.tell()
    try:
        uploaded_file.seek(0)
        signature = uploaded_file.read(5)
    finally:
        uploaded_file.seek(position)
    if signature.startswith(b"%PDF-"):
        return "application/pdf"
    if signature.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


def recognize_document(kind, uploaded_file, *, session=None):
    setting_name = DOCUMENT_READER_SETTINGS.get(kind)
    if not setting_name:
        raise ValueError(f"Unsupported document kind: {kind}")
    url = getattr(settings, setting_name, "").strip()
    if not url:
        raise DocumentReaderResponseError("Сервис распознавания документов не настроен")
    content_type = detect_document_content_type(uploaded_file)
    if not content_type:
        raise DocumentReaderResponseError("Поддерживаются только PDF и JPG")
    uploaded_file.seek(0)
    try:
        response = (session or requests).post(
            url,
            files={"file": (uploaded_file.name, uploaded_file, content_type)},
            timeout=(settings.DOCUMENT_READER_CONNECT_TIMEOUT, settings.DOCUMENT_READER_READ_TIMEOUT),
            allow_redirects=False,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        # Do not expose service URLs, credentials or internal response bodies.
        raise DocumentReaderResponseError("Сервис распознавания документов сейчас недоступен") from exc
    if response.status_code != 200:
        raise DocumentReaderResponseError("Сервис распознавания вернул неожиданный ответ")
    try:
        payload = response.json()
    except ValueError as exc:
        raise DocumentReaderResponseError("Сервис распознавания вернул некорректный ответ") from exc
    if not isinstance(payload, dict) or payload.get("error"):
        raise DocumentReaderResponseError("Сервис не смог распознать документ")
    fields = ("flm", "uid", "id", "date", "address") if kind == "id" else (
        "vin_code", "marka", "name", "model", "year",
    )
    result = {key: value for key in fields if isinstance((value := payload.get(key)), (str, int)) and not isinstance(value, bool)}
    if not any(str(value).strip() for value in result.values()):
        raise DocumentReaderResponseError("Сервис не смог распознать данные документа")
    return result
