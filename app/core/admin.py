from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from . import models


class UserAdmin(BaseUserAdmin):
    ordering = ["id"]
    list_display = ["email", "name"]
    fieldsets = (
        (_("Title"), {"fields": ("email", "password")}),
        (_('Personal'), {"fields": ("name",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
        (_("Important Dates"), {"fields": ("last_login",)})
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "password1", "password2", "name", "is_active", "is_staff", "is_superuser"), }),
    )

    readonly_fields = ["last_login"]


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)
