from rest_framework import permissions


class HasRole(permissions.BasePermission):
    """
    Custom permission to only allow users with a certain role to access it.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return request.user.role in view.ALLOWED_ROLES
        return False
