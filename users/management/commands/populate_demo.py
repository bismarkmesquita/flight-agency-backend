import os
import random
import string
from faker import Faker
from django.core.management import BaseCommand
from django.utils import timezone
from agency.models import Customer, Reservation, Sale, Supplier
from flights.models import Airline, Airport, Flight
from users.models import User


class Command(BaseCommand):
    help = "Populate database with some demo data"
    faker = Faker()
    default_password = "agency"

    def handle(self, *args, **kwargs):
        cmd_start = timezone.now()

        if not os.environ.get("ALLOW_POPULATE_DEMO"):
            print(
                "Refusing to run: set ALLOW_POPULATE_DEMO=1 to confirm "
                "this wipes and reseeds the database."
            )
            return

        self.now = timezone.now()
        self.today = self.now.date()

        Reservation.objects.all().delete()
        Sale.objects.all().delete()
        Flight.objects.all().delete()
        Airport.objects.all().delete()
        Supplier.objects.all().delete()
        Customer.objects.all().delete()
        Airline.objects.all().delete()
        User.objects.exclude(email="bismark1816@gmail.com").delete()

        self.gen_users()
        self.gen_airlines()
        self.gen_suppliers()
        self.gen_customers()
        self.gen_airports()
        self.gen_flights()
        self.gen_sales()
        self.gen_reservations()

        timetaken = timezone.now() - cmd_start
        print("\nPopulated in {} seconds.\n".format(timetaken.seconds))

    def gen_users(self):
        self.coordinator = User.objects.create_user(
            email="manager@agency.dev",
            password="manager123",
            name="manager",
            role=User.Role.MANAGER,
        )

        self.seller = User.objects.create_user(
            email="seller@agency.dev",
            password="seller123",
            name="Seller",
            role=User.Role.SELLER,
        )

        self.users = []
        for i in range(50):
            user = User(
                email=f"user{i}@user{i}.com",
                name=f"User {i}",
                role=User.Role.SELLER,
            )
            self.users.append(user)

        User.objects.bulk_create(self.users)

        print("USERS GENERATED")

    def gen_airlines(self):
        airlines = [
            ("LATAM", "LA"),
            ("Gol", "G3"),
            ("Azul", "AD"),
            ("American Airlines", "AA"),
            ("United", "UA"),
        ]
        self.airlines = [
            Airline(name=name, iata=iata) for name, iata in airlines
        ]
        Airline.objects.bulk_create(self.airlines)
        self.airlines = list(Airline.objects.all())
        print("AIRLINES GENERATED")

    def gen_suppliers(self):
        self.suppliers = []
        for _ in range(10):
            self.suppliers.append(
                Supplier(
                    name=self.faker.company(),
                    tax_id=self.faker.msisdn()[:15],
                    phone=self.faker.msisdn()[:15],
                    country=self.faker.country(),
                    city=self.faker.city(),
                    state=self.faker.state()[:2],
                    postal_code=self.faker.postcode(),
                    neighborhood=self.faker.street_name(),
                    address=self.faker.street_address(),
                    address_number=str(random.randint(1, 999)),
                )
            )

        Supplier.objects.bulk_create(self.suppliers)
        self.suppliers = list(Supplier.objects.all())
        print("SUPPLIERS GENERATED")

    def gen_customers(self):
        self.customers = []
        for _ in range(100):
            self.customers.append(
                Customer(
                    name=self.faker.name(),
                    email=self.faker.unique.email(),
                    phone=self.faker.msisdn()[:10]
                )
            )

        Customer.objects.bulk_create(self.customers)
        self.customers = list(Customer.objects.all())
        print("CUSTOMERS GENERATED")

    def random_code(self, n):
        return ''.join(random.choices(string.ascii_uppercase, k=n))

    def gen_airports(self):
        self.airports = []
        used_iata = set()
        used_icao = set()

        for _ in range(50):
            iata = self.random_code(3)
            while iata in used_iata:
                iata = self.random_code(3)

            icao = self.random_code(4)
            while icao in used_icao:
                icao = self.random_code(4)

            used_iata.add(iata)
            used_icao.add(icao)

            city = self.faker.city()
            self.airports.append(
                Airport(
                    iata=iata,
                    icao=icao,
                    name=f"{city} International Airport",
                    city=city,
                    country=self.faker.country()
                )
            )

        Airport.objects.bulk_create(self.airports)
        self.airports = list(Airport.objects.all())
        print("AIRPORTS GENERATED")

    def gen_flights(self):
        year_start = self.today.replace(month=1, day=1)
        year_end = self.today.replace(month=12, day=31)

        self.flights = []
        for _ in range(50):
            airline = random.choice(self.airlines)
            dep_date = timezone.make_aware(
                self.faker.date_time_between(
                    start_date=year_start, end_date=year_end
                )
            )
            arr_date = dep_date + timezone.timedelta(
                hours=random.randint(1, 12)
            )
            self.flights.append(
                Flight(
                    flight_number=random.randint(100, 9999),
                    airline=airline,
                    departure_date=dep_date,
                    departure_airport=random.choice(self.airports),
                    arrival_date=arr_date,
                    arrival_airport=random.choice(self.airports),
                )
            )

        Flight.objects.bulk_create(self.flights)
        self.flights = list(Flight.objects.all())
        print("FLIGHTS GENERATED")

    def gen_sales(self):
        payments = [choice[0] for choice in Sale.Payment.choices]
        year_start = self.today.replace(month=1, day=1)
        year_end = self.today.replace(month=12, day=31)

        self.sales = []
        for _ in range(100):
            amount = random.randint(500, 5000)
            cost = amount - random.randint(50, 500)
            type = random.choice([Sale.Type.B2C, Sale.Type.B2B])

            customer = random.choice(self.customers)
            self.sales.append(
                Sale(
                    seller=self.seller,
                    customer=customer,
                    type=type,
                    payment=random.choice(payments),
                    amount_received=amount,
                    cost=cost,
                    sale_date=self.faker.date_between(
                        start_date=year_start, end_date=year_end
                    ),
                    indication=random.choice([None, self.faker.first_name()]),
                )
            )

        Sale.objects.bulk_create(self.sales)
        self.sales = list(Sale.objects.all())
        print("SALES GENERATED")

    def gen_reservations(self):
        reservations = []

        for _ in range(100):
            passenger_count = random.randint(1, 4)

            reservation = Reservation.objects.create(
                locator=self.faker.unique.bothify(text="???###"),
                sale=random.choice(self.sales),
                supplier=random.choice(self.suppliers),
                issuer=random.choice(self.users),
                passenger_count=passenger_count,
                passengers=", ".join(
                    self.faker.name() for _ in range(passenger_count)
                ),
            )

            flights = random.sample(
                self.flights,
                k=random.randint(1, min(4, len(self.flights)))
            )

            reservation.flights.set(flights)

            reservations.append(reservation)

        self.reservations = reservations
        print("RESERVATIONS GENERATED")
