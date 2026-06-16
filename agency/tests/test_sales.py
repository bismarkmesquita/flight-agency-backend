

from agency.failures import CreateSaleFailureReason
from agency.models import Reservation, Sale
from core.tests import BaseTestCase
from django.utils import timezone


class CreateSaleTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "type": Sale.Type.B2B,
            "payment": Sale.Payment.DEBIT_CARD,
            "sale_date": timezone.now().date().isoformat(),
            "seller_id": self.seller.id,
            "customer_id": self.customer.id,
            "amount_received": 50,
            "cost": 20,
            "indication": "User",
        }

        self.url = "/agency/sales/"

    def test_cannot_create_without_auth(self):
        response = self.client.post(
            self.url,
            data=self.data,
        )

        self.assertEqual(response.status_code, 401)

    def test_create_sale_success(self):
        """Create sale successfully."""

        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertTrue(
            Sale.objects.filter(
                seller=self.seller,
                payment=Sale.Payment.DEBIT_CARD
            ).exists()
        )

    def test_missing_fields(self):
        """Create sale without required fields."""

        data = {"customer_id": self.customer.id}
        response = self.client.post(
            self.url,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateSaleFailureReason.MISSING_FIELDS.value
        )

    def assert_validated_data(
        self,
        field,
        value,
        expected_message,
        failure_reason,
    ):
        data = self.data.copy()
        data[field] = value

        response = self.client.post(
            self.url,
            data=data,
            headers=self.admin_token,
        )

        data = response.data

        self.assertFalse(data["success"])
        self.assertIn(expected_message, data["message"])
        self.assertEqual(failure_reason, data["reason"])

    def test_invalid_amount_received(self):
        """Invalid amount_received format."""

        self.assert_validated_data(
            "amount_received", "amount_received",
            "Invalid numeric values.",
            CreateSaleFailureReason.VALIDATION_ERROR.value
        )

        self.assert_validated_data(
            "amount_received", 0,
            "Amount received must be greater than zero.",
            CreateSaleFailureReason.VALIDATION_ERROR.value
        )

    def test_invalid_cost(self):
        """Invalid cost format."""

        self.assert_validated_data(
            "cost", "cost",
            "Invalid numeric values.",
            CreateSaleFailureReason.VALIDATION_ERROR.value
        )

        self.assert_validated_data(
            "cost", -100,
            "Cost cannot be negative.",
            CreateSaleFailureReason.VALIDATION_ERROR.value
        )

    def test_customer_not_found(self):
        self.assert_validated_data(
            "customer_id", 9999,
            "Customer not found.",
            CreateSaleFailureReason.OBJECT_NOT_FOUND.value,
        )

    def test_seller_not_found(self):
        self.assert_validated_data(
            "seller_id", 9999,
            "Seller not found.",
            CreateSaleFailureReason.OBJECT_NOT_FOUND.value,
        )

    def test_seller_must_be_provided(self):
        self.assert_validated_data(
            "seller_id", "",
            "A seller needs to be provided.",
            CreateSaleFailureReason.MISSING_FIELDS.value,
        )

    def test_seller_uses_his_only_id(self):
        data = self.data.copy()
        data["seller_id"] = self.issuer.id

        Reservation.objects.all().delete()
        Sale.objects.all().delete()

        response = self.client.post(
            self.url,
            data=data,
            headers=self.seller_token,
        )

        sale = Sale.objects.get(id=response.data["sale_id"])

        self.assertTrue(response.data["success"])
        self.assertEqual(sale.seller, self.seller)
