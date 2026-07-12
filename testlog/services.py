from django.contrib.auth.models import User
from django.db import transaction

from subuser.models import SubUser


def _available_testlog_username(owner):
    max_length = SubUser._meta.get_field("username").max_length
    base = f"{owner.username}_testlog"
    username = base[:max_length]
    suffix = 1

    while (
        User.objects.filter(username=username).exists()
        or SubUser.objects.filter(username=username).exists()
    ):
        suffix += 1
        suffix_text = f"_{suffix}"
        username = f"{base[:max_length - len(suffix_text)]}{suffix_text}"

    return username


def get_or_create_testlog_creator(user, creator_id=None):
    if not isinstance(user, User) or not user.pk or not user.is_superuser:
        return None, False

    if creator_id and str(creator_id).isdigit():
        creator = SubUser.objects.filter(pk=creator_id, is_active=True).first()
        if creator:
            return creator, False

    with transaction.atomic():
        owner = (
            User.objects.select_for_update()
            .filter(pk=user.pk, is_active=True, is_superuser=True)
            .first()
        )
        if owner is None:
            return None, False

        creator = (
            SubUser.objects.filter(creator=owner, is_active=True)
            .order_by("id")
            .first()
        )
        if creator:
            return creator, False

        creator = SubUser.objects.create_user(
            username=_available_testlog_username(owner),
            password=None,
            creator=owner,
            is_active=True,
            first_name=owner.first_name,
            last_name=owner.last_name,
            email=owner.email or "",
            sign="",
        )
        return creator, True
