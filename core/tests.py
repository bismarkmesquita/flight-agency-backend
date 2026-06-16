from django.test import TestCase
from django.utils import timezone
from agency.models import Customer, Reservation, Sale, Supplier
from flights.models import Airline, Airport, Flight
from users.models import User
from utils.test_utils import get_auth_header


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.admin_token, self.admin = get_auth_header(role=User.Role.ADMIN)
        self.manager_token, self.manager = get_auth_header(
            role=User.Role.MANAGER
        )
        self.seller_token, self.seller = get_auth_header(
            role=User.Role.SELLER
        )
        self.issuer_token, self.issuer = get_auth_header(
            role=User.Role.SELLER
        )

        self.customer = Customer.objects.create(
            name="Customer",
            email="customer@email.com",
            phone="11999999999"
        )

        self.supplier = Supplier.objects.create(
            name="Supplier 1",
            tax_id="12345678900012"
        )

        self.airline = Airline.objects.create(
            name="Companhia Aérea 1",
            iata="LA"
        )

        self.departure_airport = Airport.objects.create(
            iata="AI1",
            icao="AI10",
            name="Airport 1",
            city="City 1",
            country="Country 1",
        )

        self.arrival_airport = Airport.objects.create(
            iata="AI2",
            icao="AI20",
            name="Airport 2",
            city="City 2",
            country="Country 2",
        )

        self.flight = Flight.objects.create(
            flight_number="100",
            airline=self.airline,
            departure_date=timezone.make_aware(
                timezone.datetime(2025, 8, 21, 0, 0, 0)
            ),
            arrival_date=timezone.make_aware(
                timezone.datetime(2025, 8, 22, 0, 0, 0)
            ),
            departure_airport=self.departure_airport,
            arrival_airport=self.arrival_airport,
        )

        self.sale = Sale.objects.create(
            seller=self.seller,
            customer=self.customer,
            type=Sale.Type.B2B,
            payment=Sale.Payment.CREDIT_CARD,
            amount_received=300,
            cost=200,
            sale_date=timezone.now(),
            indication="Melina"
        )

        self.reservation = Reservation.objects.create(
            locator="LA1234",
            sale=self.sale,
            passenger_count=2,
            passengers="Melina, Torrent",
            supplier=self.supplier,
            issuer=self.issuer,
        )
        self.reservation.flights.add(self.flight)
