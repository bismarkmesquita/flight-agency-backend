from agency.failures import CreateReservationFailureReason
from agency.models import Reservation
from core.tests import BaseTestCase


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
        self.assertEqual(len(response.data["items"]), 1)

        reservation = response.data["items"][0]
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
            "locator": "ABC123",
            "sale_id": self.sale.id,
            "flight_ids": [self.flight.id],
            "supplier_id": self.supplier.id,
            "issuer_id": self.issuer.id,
            "passenger_count": 2,
            "passengers": "Passenger 1, Passenger 2",
        }

        self.url = "/agency/reservations/"

    def test_create_without_auth(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 401)

    def test_create_reservation_success(self):
        """Create reservation successfully"""
        response = self.client.post(
            self.url,
            data=self.data,
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        reservation = Reservation.objects.get(locator="ABC123")

        self.assertEqual(reservation.sale, self.sale)
        self.assertEqual(reservation.supplier, self.supplier)
        self.assertEqual(reservation.flights.count(), 1)
        self.assertEqual(reservation.flights.first().id, self.flight.id)

    def test_missing_fields(self):
        """Required fields are missing"""
        data = {"locator": "ABC123"}
        response = self.client.post(
            self.url,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.MISSING_FIELDS.value
        )

    def assert_related_entity_not_found(self, field, value):
        data = self.data.copy()
        data[field] = value

        response = self.client.post(
            self.url,
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.OBJECT_NOT_FOUND.value
        )

    def test_sale_not_found(self):
        self.assert_related_entity_not_found("sale_id", 9999)

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
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateReservationFailureReason.ALREADY_REGISTERED.value
        )
