from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from django.conf import settings


DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def save_docx(document, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document.save(destination)
    return destination


def convert_to(path, timeout=None):
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    destination_path = source_path.with_suffix(".pdf")
    converter_url = settings.PDF_CONVERTER_URL.rstrip("/")
    timeout = timeout or settings.PDF_CONVERTER_TIMEOUT
    temporary_path = None

    try:
        with source_path.open("rb") as source_file:
            with requests.post(
                f"{converter_url}/forms/libreoffice/convert",
                files={
                    "files": (
                        source_path.name,
                        source_file,
                        DOCX_CONTENT_TYPE,
                    )
                },
                data={
                    "exportFormFields": "false",
                    "losslessImageCompression": "true",
                    "reduceImageResolution": "false",
                    "updateIndexes": "false",
                },
                stream=True,
                timeout=(5, timeout),
            ) as response:
                response.raise_for_status()

                first_bytes = b""
                with NamedTemporaryFile(
                    mode="wb",
                    dir=destination_path.parent,
                    prefix=f".{destination_path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    for chunk in response.iter_content(chunk_size=64 * 1024):
                        if not chunk:
                            continue
                        if len(first_bytes) < 5:
                            first_bytes += chunk[: 5 - len(first_bytes)]
                        temporary_file.write(chunk)

                if not first_bytes.startswith(b"%PDF-"):
                    raise OSError("PDF converter returned an invalid response")

                temporary_path.chmod(0o644)
                temporary_path.replace(destination_path)
                temporary_path = None
    except requests.RequestException as exc:
        raise OSError(f"PDF converter request failed: {exc}") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return destination_path
