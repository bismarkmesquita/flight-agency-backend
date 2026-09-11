from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsFullUser


WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


class BaseAPIView(APIView):
    permission_classes = [IsAuthenticated]
    restrict_write_to_full_user = True

    def get_permissions(self):
        permissions = [permission() for permission in self.permission_classes]

        if self.restrict_write_to_full_user and self.request.method in WRITE_METHODS:
            permissions.append(IsFullUser())

        return permissions

    def error_response(self, *, message, reason, errors=None):
        return Response({
            "success": False,
            "message": message,
            "reason": reason,
            "errors": errors,
        })

    def success_response(self, *, data=None, message=None):
        return Response({
            "success": True,
            "data": data,
            "message": message,
        })
