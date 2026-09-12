from rest_framework import permissions
from users.models import User


class HasRole(permissions.BasePermission):
    """
    Custom permission to only allow users with a certain role to access it.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return request.user.role in view.ALLOWED_ROLES
        return False


class IsFullUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        return (
            user.is_authenticated
            and user.access_level == User.AccessLevel.FULL
        )
