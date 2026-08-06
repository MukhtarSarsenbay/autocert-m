from hashlib import sha256

from subuser.models import SubUser


def build_signed_document_key(sbkts, signature_content):
    signature_version = sha256(signature_content).hexdigest()[:12]
    return f"{sbkts}_{signature_version}", signature_version


class SignatureCertificateLookupError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def resolve_signature_certificate(manager, certificate_id=None, vin=None):
    """Resolve the exact certificate; never guess when a VIN is duplicated."""
    if certificate_id:
        try:
            certificate = manager.get(pk=certificate_id)
        except (manager.model.DoesNotExist, TypeError, ValueError):
            raise SignatureCertificateLookupError(
                "Сертификат не найден.", status_code=404
            )

        if vin and certificate.carVin != str(vin):
            raise SignatureCertificateLookupError(
                "VIN не соответствует выбранному сертификату."
            )
        return certificate

    if vin is None:
        raise SignatureCertificateLookupError("Не указан сертификат.")

    certificates = list(manager.filter(carVin=str(vin))[:2])
    if not certificates:
        raise SignatureCertificateLookupError(
            "Сертификат не найден.", status_code=404
        )
    if len(certificates) > 1:
        raise SignatureCertificateLookupError(
            "Для этого VIN найдено несколько сертификатов. "
            "Закройте окно подписи и откройте его заново из нужного сертификата."
        )
    return certificates[0]


def resolve_certificate_creator(certificate, request_user):
    """Restore the creator for legacy certificates when the signer is a SubUser."""
    if certificate.creator_id:
        return certificate.creator

    if isinstance(request_user, SubUser):
        certificate.creator = request_user
        certificate.save(update_fields=["creator"])
        return request_user

    return None
