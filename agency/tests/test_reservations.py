from agency.failures import CreateReservationFailureReason
from agency.models import Reservation, Sale
from core.tests import BaseTestCase
from rest_framework import status


class GetReservationsTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.url = "/agency/reservations/"

    def test_get_reservations_list(self):
        """try get reservations list"""

        response = self.client.get(
            "/agency/reservations/",
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["data"]), 1)

        reservation = response.data["data"][0]
        self.assertEqual(
            reservation["locator"],
            self.reservation.locator,
        )

    def test_cannot_access_without_auth(self):
        """try accessing without authentication."""

        response = self.client.get("/agency/reservations/")

        assert response.status_code == 401


class CreateReservationTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.data = {
            "sale": {
                "seller_id": self.sale.seller.id,
                "customer_id": self.sale.customer.id,
                "type": self.sale.type,
                "payment": self.sale.payment,
                "amount_received": self.sale.amount_received,
                "cost": self.sale.cost,
                "sale_date": self.sale.sale_date.isoformat(),
                "indication": self.sale.indication,
            },
            "reservation": {
                "locator": "ABC123",
                "flight_ids": [self.flight.id],
                "supplier_id": self.supplier.id,
                "issuer_id": self.issuer.id,
                "passenger_count": 2,
                "passengers": "Passenger 1, Passenger 2",
            }
        }

        self.url = "/agency/reservations/"

    def test_create_without_auth(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 401)

    def test_create_reservation_success(self):
        """Create sale and reservation successfully"""

        sale_count = Sale.objects.count()
        reservation_count = Reservation.objects.count()

        response = self.client.post(
            self.url,
            data=self.data,
            content_type="application/json",
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])

        self.assertEqual(Sale.objects.count(), sale_count + 1)
        self.assertEqual(Reservation.objects.count(), reservation_count + 1)

        reservation = Reservation.objects.get(locator="ABC123")
        sale = reservation.sale

        self.assertNotEqual(sale.id, self.sale.id)
        self.assertEqual(sale.seller, self.sale.seller)
        self.assertEqual(sale.customer, self.sale.customer)
        self.assertEqual(sale.type, self.sale.type)
        self.assertEqual(sale.payment, self.sale.payment)
        self.assertEqual(sale.amount_received, self.sale.amount_received)
        self.assertEqual(sale.cost, self.sale.cost)
        self.assertEqual(sale.sale_date, self.sale.sale_date)

        self.assertEqual(reservation.supplier, self.supplier)
        self.assertEqual(reservation.issuer, self.issuer)
        self.assertEqual(reservation.passenger_count, 2)
        self.assertEqual(reservation.passengers, "Passenger 1, Passenger 2")
        self.assertEqual(reservation.flights.count(), 1)
        self.assertEqual(reservation.flights.first().id, self.flight.id)

    def test_demo_user_cannot_create_reservation(self):
            Reservation.objects.all().delete()
            Sale.objects.all().delete()
    
            response = self.client.post(
                self.url,
                data=self.data,
                headers=self.demo_token,
            )
    
            reservations = Reservation.objects.all().count()
    
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(reservations, 0)

    def test_missing_fields(self):
        """Required fields are missing"""
        data = {"sale": self.data["sale"]}
        response = self.client.post(
            self.url,
            data=data,
            content_type="application/json",
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.MISSING_FIELDS.value
        )

    def assert_validated_sale_data(
        self,
        field,
        value,
        expected_message,
    ):
        data = self.data.copy()
        data["sale"][field] = value

        response = self.client.post(
            self.url,
            data=data,
            content_type="application/json",
            headers=self.admin_token,
        )

        data = response.data

        self.assertFalse(data["success"])
        self.assertIn(expected_message, data["message"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.VALIDATION_ERROR.value
        )

    def test_invalid_amount_received(self):
        """Invalid amount_received format."""

        self.assert_validated_sale_data(
            "amount_received", "amount_received",
            "Invalid numeric values.",
        )

        self.assert_validated_sale_data(
            "amount_received", 0,
            "Amount received must be greater than zero.",
        )

    def test_invalid_cost(self):
        """Invalid cost format."""

        self.assert_validated_sale_data(
            "cost", "cost",
            "Invalid numeric values.",
        )

        self.assert_validated_sale_data(
            "cost", -100,
            "Cost cannot be negative.",
        )

    def assert_related_entity_not_found(self, field, value):
        data = self.data.copy()
        data["reservation"][field] = value

        response = self.client.post(
            self.url,
            data=data,
            content_type="application/json",
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.OBJECT_NOT_FOUND.value
        )

    def test_supplier_not_found(self):
        self.assert_related_entity_not_found("supplier_id", 9999)

    def test_issuer_not_found(self):
        self.assert_related_entity_not_found("issuer_id", 9999)

    def test_flight_not_found(self):
        self.assert_related_entity_not_found("flight_ids", [999])

    def test_existing_reservation(self):
        """Existing reservation"""

        reservation = Reservation.objects.create(
            locator="ABC123",
            sale_id=self.sale.id,
            supplier_id=self.supplier.id,
            issuer_id=self.issuer.id,
            passenger_count=2,
            passengers="Passenger 1, Passenger 2",
        )
        reservation.flights.add(self.flight.id)

        response = self.client.post(
            self.url,
            data=self.data,
            content_type="application/json",
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.ALREADY_REGISTERED.value
        )

    def test_sale_is_not_created_when_reservation_fails(self):
        sale_count = Sale.objects.count()

        data = self.data.copy()
        data["reservation"] = self.data["reservation"].copy()
        data["reservation"]["supplier_id"] = 9999

        response = self.client.post(
            self.url,
            data=data,
            content_type="application/json",
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])

        self.assertEqual(Sale.objects.count(), sale_count)

        self.assertFalse(
            Reservation.objects.filter(
                locator="ABC123"
            ).exists()
        )

    def test_seller_uses_his_only_id(self):
        data = self.data.copy()
        data["sale"]["seller_id"] = self.issuer.id

        Reservation.objects.all().delete()
        Sale.objects.all().delete()

        response = self.client.post(
            self.url,
            data=data,
            content_type="application/json",
            headers=self.seller_token,
        )

        self.assertTrue(response.data["success"])

        sale = Sale.objects.get(id=response.data["data"]["sale_id"])

        self.assertEqual(sale.seller, self.seller)
