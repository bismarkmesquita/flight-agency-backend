from django.contrib import admin
from users.models import User


class BaseAdmin(admin.ModelAdmin):
    admin_role = User.Role.ADMIN

    def _has_permission(self, request):
        return (
            request.user.is_authenticated
            and request.user.role == self.admin_role
        )

    def has_module_permission(self, request):
        return self._has_permission(request)

    def has_view_permission(self, request, obj=None):
        return self._has_permission(request)

    def has_add_permission(self, request):
        return self._has_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self._has_permission(request)
