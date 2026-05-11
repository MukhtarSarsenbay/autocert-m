from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline
from .models import SubUser

from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

from django.utils.translation import gettext_lazy as _

from .models import Profile
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

class ProfileInline(StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'

@admin.register(SubUser)
class SubUserAdmin(UserAdmin, ModelAdmin):
    autocomplete_fields = ["creator"]
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "first_name", "last_name", "creator", "is_staff",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    	(_("Доступ и подпись"), {"fields": ("creator","sign")})
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creator=request.user)


admin.site.unregister(User)
@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    inlines = (ProfileInline,)
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs.filter()

        return qs.filter(id = request.user.id)


admin.site.unregister(Group)
@admin.register(Group)
class CustomGroupAdmin(GroupAdmin, ModelAdmin):
    pass