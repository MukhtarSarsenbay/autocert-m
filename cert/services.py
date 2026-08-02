from subuser.models import SubUser


def resolve_certificate_creator(certificate, request_user):
    """Restore the creator for legacy certificates when the signer is a SubUser."""
    if certificate.creator_id:
        return certificate.creator

    if isinstance(request_user, SubUser):
        certificate.creator = request_user
        certificate.save(update_fields=["creator"])
        return request_user

    return None
