from django.utils import timezone
from core.tests import BaseTestCase
from users.models import InternalLog, User
from users.failures import (
    CreateOrUpdateUserFailureReason,
    LoginViewFailureReason,
)


class BaseUsersTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.now = timezone.now()


class LoginViewTests(BaseUsersTestCase):
    def setUp(self):
        super().setUp()

    def test_login(self):
        response = self.client.post(
            "/auth/login/",
            {
                "login": self.seller.email,
                "password": "123456789",
            },
        )
        self.assertEqual(response.data["user"]["email"], self.seller.email)

    def test_validations(self):
        # try login with wrong password
        response = self.client.post(
            "/auth/login/",
            {
                "login": self.seller.email,
                "password": "wrong",
            },
        )

        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(
            data["reason"], LoginViewFailureReason.INVALID_CREDENTIALS.value
        )


class CreateOrUpdateUserViewTests(BaseUsersTestCase):
    def setUp(self):
        super().setUp()

        self.url_create = "/auth/create/"
        self.url_update = "/auth/update/"

    def test_create_user_success(self):
        """Create a new user successfully."""
        data = {
            "name": "New User",
            "email": "new@example.com",
            "role": User.Role.SELLER,
        }

        response = self.client.post(
            self.url_create,
            data=data,
            headers=self.admin_token,
        )
        user = User.objects.filter(email="new@example.com").exists()

        self.assertTrue(response.data["success"])
        self.assertTrue(user)
        self.assertTrue(InternalLog.objects.exists())

    def test_missing_fields(self):
        """Create a new user missing fields."""
        data = {
            "name": "New User",
            "role": User.Role.SELLER,
        }

        response = self.client.post(
            self.url_create,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateOrUpdateUserFailureReason.MISSING_FIELDS.value,
        )

    def test_invalid_email(self):
        """Do not create a user with invalid email."""
        data = {
            "name": "User",
            "email": "invalid-email",
            "role": User.Role.SELLER,
        }

        response = self.client.post(
            self.url_create,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateOrUpdateUserFailureReason.INVALID_EMAIL.value
        )

    def test_invalid_role(self):
        """Do not create a user with invalid role."""
        data = {
            "name": "User",
            "email": "email@email.com",
            "role": "invalid-role",
        }

        response = self.client.post(
            self.url_create,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateOrUpdateUserFailureReason.INVALID_ROLE.value
        )

    def test_create_user_duplicate_email(self):
        """Do not create a user if the email already exists."""
        data = {
            "name": "Duplicate",
            "email": self.seller.email,
            "role": User.Role.SELLER,
        }

        response = self.client.post(
            self.url_create,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateOrUpdateUserFailureReason.ALREADY_REGISTERED.value
        )

    def test_update_user_success(self):
        """Edit an existing user successfully."""
        data = {
            "name": "Edited Seller",
            "email": self.seller.email,
            "role": User.Role.SELLER,
        }

        response = self.client.put(
            f"{self.url_update}{self.seller.id}/",
            data=data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.seller.refresh_from_db()

        self.assertTrue(response.data["success"])
        self.assertEqual(self.seller.name, "Edited Seller")

    def test_create_user_denied_for_not_allowed_roles(self):
        """Test create user denied for not allowed roles"""

        data = {
            "name": "New User",
            "email": "new@example.com",
            "role": User.Role.SELLER,
        }

        response = self.client.post(
            self.url_create,
            data=data,
            headers=self.seller_token,
        )
        user = User.objects.filter(email="new@example.com").exists()

        self.assertEqual(response.status_code, 403)
        self.assertFalse(user)
        self.assertFalse(InternalLog.objects.exists())

    def test_edit_user_not_found(self):
        """Do not edit if the user does not exist."""
        data = {
            "name": "Non-existent",
            "email": "notfound@example.com",
            "role": User.Role.SELLER,
        }

        response = self.client.put(
            f"{self.url_update}333/",
            data=data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateOrUpdateUserFailureReason.INVALID_USER.value
        )

    def test_edit_user_email_conflict(self):
        """Do not edit if the email address is already in use by another user."""
        other_user = User.objects.create_user(
            name="Other",
            email="other@example.com",
            role=User.Role.SELLER,
        )

        data = {
            "name": "Trying to duplicate",
            "email": self.seller.email,
            "role": User.Role.SELLER,
        }

        response = self.client.put(
            f"{self.url_update}{other_user.id}/",
            data=data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateOrUpdateUserFailureReason.ALREADY_REGISTERED.value
        )


class GetUsersViewTests(BaseUsersTestCase):
    def setUp(self):
        super().setUp()

    def test_get_users_list(self):
        # try get users list without admin
        response = self.client.get("/auth/users/", headers=self.admin_token)

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 4)

    def test_cannot_access_whithout_auth(self):
        # try accessing without authentication.
        response = self.client.get("/auth/users/")

        assert response.status_code == 401
