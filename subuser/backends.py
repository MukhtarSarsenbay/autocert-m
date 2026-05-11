from django.contrib.auth.backends import ModelBackend
from .models import SubUser

from django.contrib.auth.models import Permission, User
from django.db.models import Exists, OuterRef, Q


class SubUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = SubUser.objects.get(username=username)
        except SubUser.DoesNotExist:
            return None
        #print(user, user.check_password(password))
        if user.check_password(password) and self.user_can_authenticate(user) and user.creator.is_active:
            return user


    def _get_user_permissions(self, user_obj):
        return user_obj.user_permissions.all()

    def _get_group_permissions(self, user_obj):
        print("get_group_permissions", user_obj)
        if SubUser.objects.filter(username = user_obj.username):
            user_groups_field = SubUser._meta.get_field("groups")
            user_groups_query = "group__%s" % user_groups_field.related_query_name()
            return Permission.objects.filter(**{user_groups_query: user_obj})
        else:
            user_groups_field = User._meta.get_field("groups")
            user_groups_query = "group__%s" % user_groups_field.related_query_name()
            return Permission.objects.filter(**{user_groups_query: user_obj})

    def get_user_permissions(self, user_obj, obj=None):
        """
        Return a set of permission strings the user `user_obj` has from their
        `user_permissions`.
        """
        return self._get_permissions(user_obj, obj, "user")

    def get_group_permissions(self, user_obj, obj=None):
        """
        Return a set of permission strings the user `user_obj` has from the
        groups they belong.
        """
        return self._get_permissions(user_obj, obj, "group")

    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        if not hasattr(user_obj, "_perm_cache"):
            user_obj._perm_cache = super().get_all_permissions(user_obj)
        return user_obj._perm_cache

    def get_user(self, user_id):
        try:
            user = SubUser.objects.get(pk=user_id)
        except SubUser.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def with_perm(self, perm, is_active=True, include_superusers=True, obj=None):
        if isinstance(perm, str):
            try:
                app_label, codename = perm.split('.')
            except ValueError:
                raise ValueError(
                    "Permission name should be in the form"
                    "app_label.permission_codename."
                )
        elif not isinstance(perm, Permission):
            raise TypeError(
                "The `perm` argument must be a string or a permission instance."
            )


        if obj is not None:
            return SubUser.objects.none()

        permission_q = Q(group__user=OuterRef("pk")) | Q(user=OuterRef("pk"))
        if isinstance(perm, Permission):
            permission_q &= Q(pk=perm.pk)
        else:
            permission_q &= Q(codename=codename, content_type__app_label=app_label)

        user_q = Exists(Permission.objects.filter(permission_q))
        if include_superusers:
            user_q |= Q(is_superuser=True)
        if is_active is not None:
            user_q &= Q(is_active=is_active)

        print(user_q)

        return SubUser.objects.filter(user_q)
