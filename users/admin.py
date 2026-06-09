from core.admin import BaseAdmin
from django.contrib import admin
from users.models import InternalLog, User


class UserAdmin(BaseAdmin):
    list_display = [
        "name",
        "email",
        "last_access",
    ]
    search_fields = ["name", "email"]
    exclude = [
        "first_name",
        "last_name",
        "groups",
        "user_permissions",
        "is_staff",
        "is_superuser",
    ]
    readonly_fields = ["last_access"]
    list_filter = ["role"]

    def has_view_permission(self, request, obj=None):
        if (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_superuser
        ):
            return True
        return False

    def has_module_permission(self, request, obj=None):
        if (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
            and request.user.is_superuser
        ):
            return True
        return False

    ALLOWED_ROLES = [User.Role.ADMIN]


class InternalLogAdmin(BaseAdmin):
    ALLOWED_ROLES = [User.Role.ADMIN]
    list_display = ["action", "created_at", "message"]
    list_filter = ["action"]


admin.site.register(User, UserAdmin)
admin.site.register(InternalLog, InternalLogAdmin)
