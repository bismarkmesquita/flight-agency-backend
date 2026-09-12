from agency.failures import CreateCustomerFailureReason
from agency.models import Customer, Reservation, Sale
from core.tests import BaseTestCase
from rest_framework import status


class GetCustomersTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_get_customers_list(self):
        """try get customers list"""

        response = self.client.get(
            "/agency/customers/",
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

    def test_cannot_access_whithout_auth(self):
        """try accessing without authentication."""

        response = self.client.get("/agency/customers/")

        assert response.status_code == 401


class GetCustomerTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def get_url(self, customer_id):
        return f"/agency/customers/{customer_id}/"

    def test_get_customer_success(self):
        response = self.client.get(
            self.get_url(self.customer.id),
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["id"],
            self.customer.id,
        )

    def test_get_customer_not_found(self):
        response = self.client.get(
            self.get_url(9999),
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.INVALID_CUSTOMER.value,
        )

    def test_get_customer_without_auth(self):
        response = self.client.get(
            self.get_url(self.customer.id),
        )

        self.assertEqual(response.status_code, 401)


class DeleteCustomerTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def get_url(self, customer_id):
        return f"/agency/customers/{customer_id}/"

    def test_delete_customer_success(self):
        response = self.client.delete(
            self.get_url(self.customer.id),
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])

        self.customer.refresh_from_db()
        self.assertFalse(self.customer.is_active)

    def test_demo_user_cannot_delete_customer(self):
        response = self.client.delete(
            self.get_url(self.customer.id),
            headers=self.demo_token,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_customer_not_found(self):
        response = self.client.delete(
            self.get_url(9999),
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.INVALID_CUSTOMER.value,
        )

    def test_delete_customer_without_auth(self):
        response = self.client.delete(
            self.get_url(self.customer.id),
        )

        self.assertEqual(response.status_code, 401)


class CreateCustomerTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "name": "Michael Jackson",
            "email": "michael@example.com",
            "phone": "+5511987654321",
        }

        self.url = "/agency/customers/"

    def test_create_customer_success(self):
        """Create customer successfully."""

        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertTrue(
            Customer.objects.filter(email=self.data["email"]).exists()
        )

    def test_demo_user_cannot_create_customer(self):
        Reservation.objects.all().delete()
        Sale.objects.all().delete()
        Customer.objects.all().delete()

        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.demo_token,
        )

        customers = Customer.objects.all().count()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(customers, 0)

    def test_missing_fields(self):
        """Create customer without required fields."""

        data = {"name": "Michael Jackson"}
        response = self.client.post(
            self.url,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.MISSING_FIELDS.value
        )

    def test_invalid_email(self):
        """Invalid email format."""

        self.data["email"] = "invalid_email"
        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.INVALID_EMAIL.value
        )

    def test_existing_customer(self):
        """Customer already registered."""

        Customer.objects.create(
            name="Michael Jackson",
            email=self.data["email"],
            phone=self.data["phone"],
        )

        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.ALREADY_REGISTERED.value
        )


class UpdateCustomerTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "name": "Michael Jackson",
            "email": "michael@example.com",
            "phone": "+5511987654321",
        }

    def get_url(self, customer_id):
        return f"/agency/customers/{customer_id}/"

    def test_update_customer_success(self):
        """Update customer successfully."""

        updated_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "phone": "+5511888888888",
        }

        response = self.client.put(
            self.get_url(self.customer.id),
            data=updated_data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertTrue(response.data["success"])

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, updated_data["name"])
        self.assertEqual(self.customer.email, updated_data["email"])
        self.assertEqual(self.customer.phone, updated_data["phone"])

    def test_demo_user_cannot_update_customer(self):
        updated_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "phone": "+5511888888888",
        }

        response = self.client.put(
            self.get_url(self.customer.id),
            data=updated_data,
            headers=self.demo_token,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_customer_not_found(self):
        """Trying to update a non-existing customer."""

        response = self.client.put(
            self.get_url(999),
            data=self.data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])

    def test_update_customer_email_already_exists(self):
        Customer.objects.create(
            name="Customer 2",
            email="b@mail.com",
            phone="22222222222"
        )

        data = {
            "name": "New Name",
            "email": "b@mail.com",
            "phone": "33333333333",
        }

        response = self.client.put(
            self.get_url(self.customer.id),
            data=data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.ALREADY_REGISTERED.value
        )

    def test_update_customer_missing_fields(self):
        response = self.client.put(
            self.get_url(self.customer.id),
            data={"name": "Only Name"},
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.MISSING_FIELDS.value,
        )

    def test_update_customer_invalid_email(self):
        data = {
            "name": "New Name",
            "email": "invalid_email",
            "phone": "99999999999",
        }

        response = self.client.put(
            self.get_url(self.customer.id),
            data=data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateCustomerFailureReason.INVALID_EMAIL.value,
        )

    def test_update_customer_keep_same_email_and_phone(self):
        data = {
            "name": "Updated Name",
            "email": self.customer.email,
            "phone": self.customer.phone,
        }

        response = self.client.put(
            self.get_url(self.customer.id),
            data=data,
            headers=self.admin_token,
            content_type="application/json",
        )

        self.assertTrue(response.data["success"])
