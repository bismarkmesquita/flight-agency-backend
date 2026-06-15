import datetime
from django.utils import timezone
from core.tests import BaseTestCase
from flights.failures import CreateFlightFailureReason
from flights.models import Flight


class GetAirlinesTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_get_airlines_list(self):
        """try get airlines list."""
        response = self.client.get(
            "/flights/airlines/", headers=self.admin_token)

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["airlines"]), 1)

    def test_cannot_access_whithout_auth(self):
        """try accessing without authentication."""
        response = self.client.get("/flights/airlines/")

        assert response.status_code == 401


class GetAirportsTests(BaseTestCase):
    def setUp(self):
        super().setUp()

    def test_get_airports_list(self):
        """try get airports list."""
        response = self.client.get(
            "/flights/airports/", headers=self.admin_token)

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["airports"]), 2)

    def test_cannot_access_whithout_auth(self):
        """try accessing without authentication."""
        response = self.client.get("/flights/airports/")

        assert response.status_code == 401


class NextFlightsTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        Flight.objects.create(
            flight_number="100",
            airline=self.airline,
            departure_date=timezone.now() + timezone.timedelta(days=1),
            arrival_date=timezone.now() + timezone.timedelta(days=2),
            departure_airport=self.departure_airport,
            arrival_airport=self.arrival_airport,
        )

    def test_get_flights_list(self):
        """try get next flights list"""

        response = self.client.get(
            "/flights/next/",
            headers=self.admin_token
        )

        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["flights"]), 1)

    def test_cannot_access_whithout_auth(self):
        """try accessing without authentication."""

        response = self.client.get("/flights/next/")

        assert response.status_code == 401


class CreateFlightTests(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.departure_date = timezone.make_aware(
            datetime.datetime(2025, 8, 21, 0, 0)
        )
        self.arrival_date = timezone.make_aware(
            datetime.datetime(2025, 8, 22, 0, 0)
        )

        self.data = {
            "flight_number": "200",
            "airline_id": self.airline.id,
            "departure_date": self.departure_date,
            "arrival_date": self.arrival_date,
            "departure_airport_id": self.departure_airport.id,
            "arrival_airport_id": self.arrival_airport.id,
        }

    def test_create_flight_success(self):
        """Create flight successfully."""

        Flight.objects.all().delete()
        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["message"],
            "Flight successfully registered."
        )
        self.assertEqual(Flight.objects.count(), 1)

    def test_missing_fields(self):
        """Create flight without fields."""

        data = {"flight_number": "1570"}
        response = self.client.post(
            "/flights/",
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.MISSING_FIELDS.value
        )

    def test_invalid_flight_number(self):
        """Invalid flight number"""

        self.data["flight_number"] = "BA"
        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.INVALID_FLIGHT_NUMBER.value
        )

    def test_invalid_airline(self):
        """Invalid airline"""

        self.data["airline_id"] = 9999
        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.INVALID_AIRLINE.value
        )

    def test_invalid_airport(self):
        """Invalid airport"""

        self.data["departure_airport_id"] = 9999
        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.INVALID_AIRPORT.value
        )

    def test_invalid_date(self):
        """Invalid date"""

        self.data["departure_date"] = "03/01/2002"
        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.INVALID_DATE.value
        )

    def test_existing_flight(self):
        """Flight already created"""
        data = {
            "flight_number": "200",
            "airline_id": self.airline.id,
            "departure_date": self.departure_date,
            "arrival_date": self.arrival_date,
            "departure_airport_id": self.departure_airport.id,
            "arrival_airport_id": self.arrival_airport.id,
        }
        Flight.objects.create(**data)

        response = self.client.post(
            "/flights/",
            data=data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.ALREADY_REGISTERED.value
        )

    def test_same_airports(self):
        self.data["arrival_airport_id"] = (self.departure_airport.id)

        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.INVALID_AIRPORT.value,
        )

    def test_arrival_before_departure(self):
        self.data["arrival_date"] = (
            timezone.make_aware(
                datetime.datetime(2025, 8, 20, 0, 0)
            )
        )

        response = self.client.post(
            "/flights/",
            data=self.data,
            headers=self.admin_token,
        )

        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["reason"],
            CreateFlightFailureReason.INVALID_DATE.value,
        )
