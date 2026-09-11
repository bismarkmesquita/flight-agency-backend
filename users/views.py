from django.contrib.auth import login, authenticate
from django.core.exceptions import ValidationError
from rest_framework import permissions
from knox.views import LoginView as KnoxLoginView
from knox.views import LogoutView as KnoxLogoutView
from knox.settings import knox_settings
from django.utils import timezone
from core.views import BaseAPIView
from core.utils import get_object_or_none
from .models import InternalLog, User
from .failures import (
    CreateOrUpdateUserFailureReason,
    LoginViewFailureReason,
)
from utils.validators import (
    validate_string,
    validate_email,
)
from users.permissions import HasRole


class LoginView(BaseAPIView, KnoxLoginView):
    permission_classes = (permissions.AllowAny,)
    restrict_write_to_full_user = False

    def __init__(self):
        super().__init__()
        self.token_ttl = knox_settings.TOKEN_TTL

    def get_token_ttl(self):
        return self.token_ttl

    def post(self, request, format=None):
        email = validate_email(request.data.get("login"))
        password = validate_string(request.data.get("password"), "password")

        user = authenticate(email=email, password=password)

        if not user:
            return self.error_response(
                message="Incorrect email or password.",
                reason=LoginViewFailureReason.INVALID_CREDENTIALS.value,
            )

        login(request, user)

        keep_connected = request.data.get("keep_connected", False)
        if keep_connected:
            self.token_ttl = timezone.timedelta(days=365)

        response = super(LoginView, self).post(request, format=None)
        return response


class LogoutView(BaseAPIView, KnoxLogoutView):
    restrict_write_to_full_user = False

    def post(self, request):
        super(LogoutView, self).post(request, format=None)
        return self.success_response()


class LastSeenView(BaseAPIView):
    restrict_write_to_full_user = False

    def post(self, request):
        """
        Updates the user's last seen date.
        """

        user = request.user
        user.last_access = timezone.now()
        user.save()
        return self.success_response()


class CreateOrUpdateUserView(BaseAPIView):
    restrict_write_to_full_user = False
    permission_classes = (HasRole,)
    ALLOWED_ROLES = [
        User.Role.ADMIN,
        User.Role.MANAGER,
    ]

    def validate_data(self, data, id=None):
        required_fields = [
            "name",
            "email",
            "role",
        ]

        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return None, self.error_response(
                message=f"Required fields: {', '.join(missing_fields)}",
                reason=CreateOrUpdateUserFailureReason.MISSING_FIELDS.value,
            )

        name = validate_string(data.get("name"), "name")
        email = validate_string(data.get("email"), "email")
        role = validate_string(data.get("role"), "role")

        try:
            validate_email(email)
        except ValidationError:
            return None, self.error_response(
                message="Invalid email address.",
                reason=CreateOrUpdateUserFailureReason.INVALID_EMAIL.value,
            )

        if role not in [
            User.Role.MANAGER,
            User.Role.SELLER,
        ]:
            return None, self.error_response(
                message="Invalid role.",
                reason=CreateOrUpdateUserFailureReason.INVALID_ROLE.value,
            )

        existing = User.objects.filter(email=email)
        if id:
            existing = existing.exclude(id=id)

        if existing.exists():
            return None, self.error_response(
                message="A user with this email address already exists.",
                reason=CreateOrUpdateUserFailureReason.ALREADY_REGISTERED.value,
            )

        return {
            "name": name,
            "email": email,
            "role": role,
        }, None

    def post(self, request, id=None):
        data, error = self.validate_data(request.data)
        if error:
            return error

        user = User.objects.create(**data)
        InternalLog.objects.create(
            action=InternalLog.Action.CREATE,
            entity="User",
            entity_id=user.id,
            message=f"Created account: {user.email}.",
            user=request.user,
        )

        return self.success_response(
            data=self.serializer(user),
            message="User successfully registered.",
        )

    def put(self, request, id):
        user = get_object_or_none(User, id=id)
        if not user:
            return self.error_response(
                message="User not found.",
                reason=CreateOrUpdateUserFailureReason.INVALID_USER.value,
            )

        if user.role == User.Role.ADMIN:
            return self.error_response(
                message="Administrator users cannot be modified.",
                reason=CreateOrUpdateUserFailureReason.INVALID_ROLE.value,
            )

        data, error = self.validate_data(request.data, id=id)
        if error:
            return error

        user.name = data["name"]
        user.email = data["email"]
        user.role = data["role"]
        user.save()

        InternalLog.objects.create(
            action=InternalLog.Action.UPDATE,
            entity="User",
            entity_id=user.id,
            message=f"Modified account: {user.email}.",
            user=request.user,
        )

        return self.success_response(
            data=self.serializer(user),
            message="User updated successfully.",
        )

    def serializer(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "email": obj.email,
            "role": obj.role,
        }


class GetUsersView(BaseAPIView):
    def get(self, request):
        users = (
            User.objects
            .exclude(role=User.Role.ADMIN)
            .order_by("name")
        )
        data = [self.serializer(user) for user in users]

        return self.success_response(data=data)

    def serializer(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "email": obj.email,
            "last_access": obj.last_access,
            "role": obj.role,
        }
