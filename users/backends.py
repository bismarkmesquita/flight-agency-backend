from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class AuthBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        email=None,
        **kwargs
    ):
        UserModel = get_user_model()

        login = email or username

        if not login:
            return None

        try:
            user = UserModel.objects.get(email=login)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
