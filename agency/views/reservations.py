from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch
from core.utils import get_object_or_none
from users.models import User
from flights.models import Flight
from agency.models import Customer, Reservation, Sale, Supplier
from agency.failures import CreateReservationFailureReason
from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_date


class ReservationMixin:
    def serialize_reservation(self, reservation):
        return {
            "id": reservation.id,
            "locator": reservation.locator,
            "passenger_count": reservation.passenger_count,
            "flights": [
                self.serialize_flight(flight)
                for flight in reservation.prefetched_flights
            ],
            "sale": self.serialize_sale(reservation.sale),
            "issuer": self.serialize_user(reservation.issuer),
            "supplier": self.serialize_supplier(reservation.supplier),
        }

    def serialize_flight(self, flight):
        return {
            "iata": flight.iata,
            "departure_airport": flight.departure_airport.iata,
            "arrival_airport": flight.arrival_airport.iata,
            "departure_date": flight.departure_date,
        }

    def serialize_sale(self, sale):
        return {
            "id": sale.id,
            "type": sale.type,
            "seller": self.serialize_user(sale.seller),
            "customer": self.serialize_user(sale.customer),
            "payment": sale.payment,
            "amount_received": sale.amount_received,
            "cost": sale.cost,
            "profit": sale.profit,
            "sale_date": sale.sale_date,
            "indication": sale.indication,
        }

    def serialize_user(self, user_field):
        return {
            "id": user_field.id,
            "name": user_field.name,
        }

    def serialize_supplier(self, supplier):
        return {
            "id": supplier.id,
            "name": supplier.name,
            "tax_id": supplier.tax_id,
        }

    def error_response(self, message, reason):
        return Response({
            "success": False,
            "message": message,
            "reason": reason,
        })

    def validate_data(self, data, user):
        sale_data = data.get("sale")
        reservation_data = data.get("reservation")

        if not isinstance(sale_data, dict):
            return None, self.error_response(
                "Sale data must be an object.",
                CreateReservationFailureReason.MISSING_FIELDS.value,
            )

        if not isinstance(reservation_data, dict):
            return None, self.error_response(
                "Reservation data must be an object.",
                CreateReservationFailureReason.MISSING_FIELDS.value,
            )

        sale_required_fields = [
            "seller_id",
            "customer_id",
            "type",
            "payment",
            "amount_received",
            "cost",
            "sale_date",
        ]

        reservation_required_fields = [
            "locator",
            "passenger_count",
            "supplier_id",
            "issuer_id",
            "flight_ids",
        ]

        missing_sale_fields = [
            field
            for field in sale_required_fields
            if sale_data.get(field) is None
        ]

        if missing_sale_fields:
            return None, self.error_response(
                f"Required sale fields: {', '.join(missing_sale_fields)}",
                CreateReservationFailureReason.MISSING_FIELDS.value,
            )

        missing_reservation_fields = [
            field
            for field in reservation_required_fields
            if reservation_data.get(field) is None
        ]

        if missing_reservation_fields:
            return None, self.error_response(
                f"Required reservation fields: {', '.join(missing_reservation_fields)}",
                CreateReservationFailureReason.MISSING_FIELDS.value,
            )

        # Validade sale values
        cost = sale_data["cost"]
        amount_received = sale_data["amount_received"]
        try:
            amount_received = Decimal(str(amount_received))
            cost = Decimal(str(cost))
        except InvalidOperation:
            return None, self.error_response(
                "Invalid numeric values.",
                CreateReservationFailureReason.VALIDATION_ERROR.value,
            )

        if amount_received <= 0:
            return None, self.error_response(
                "Amount received must be greater than zero.",
                CreateReservationFailureReason.VALIDATION_ERROR.value,
            )

        if cost < 0:
            return None, self.error_response(
                "Cost cannot be negative.",
                CreateReservationFailureReason.VALIDATION_ERROR.value,
            )

        # Validade seller
        if user.role == User.Role.SELLER:
            seller = user
        else:
            seller = get_object_or_none(User, id=sale_data["seller_id"])

            if not seller:
                return None, self.error_response(
                    "Seller not found.",
                    CreateReservationFailureReason.OBJECT_NOT_FOUND.value
                )

        # Validade customer
        customer = get_object_or_none(Customer, id=sale_data["customer_id"])
        if not customer:
            return None, self.error_response(
                "Customer not found.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        # Validate sale date
        sale_date = parse_date(sale_data["sale_date"])
        if not sale_date:
            return None, self.error_response(
                "Invalid sale date.",
                CreateReservationFailureReason.VALIDATION_ERROR.value,
            )

        # Validade supplier
        supplier_id = reservation_data["supplier_id"]
        supplier = get_object_or_none(Supplier, id=supplier_id)
        if not supplier:
            return None, self.error_response(
                "Supplier not found.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        # Validade issuer
        issuer_id = reservation_data["issuer_id"]
        issuer = get_object_or_none(User, id=issuer_id)
        if not issuer:
            return None, self.error_response(
                "Issuer not found.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        # Validade locator
        locator = reservation_data["locator"]
        if Reservation.objects.filter(locator=locator).exists():
            return None, self.error_response(
                "A reservation already exists with the provided locator number.",
                CreateReservationFailureReason.ALREADY_REGISTERED.value
            )

        # Validade flights
        flight_ids = reservation_data["flight_ids"]
        flights = list(Flight.objects.filter(id__in=set(flight_ids)))
        if len(flights) != len(set(flight_ids)):
            return None, self.error_response(
                "One or more flights do not exist.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        passengers = reservation_data.get("passengers")
        passenger_count = reservation_data["passenger_count"]

        return {
            "sale": {
                "seller": seller,
                "customer": customer,
                "type": sale_data["type"],
                "payment": sale_data["payment"],
                "amount_received": sale_data["amount_received"],
                "cost": sale_data["cost"],
                "sale_date": sale_data["sale_date"],
                "indication": sale_data.get("indication"),
            },
            "reservation": {
                "locator": locator,
                "passengers": passengers,
                "passenger_count": passenger_count,
                "supplier": supplier,
                "issuer": issuer,
                "flights": flights,
            },
        }, None


class ReservationsView(ReservationMixin, APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        flights = (
            Flight.objects
            .select_related(
                "departure_airport",
                "arrival_airport",
            )
        )

        reservations = (
            Reservation.objects
            .select_related(
                "supplier",
                "issuer",
                "sale",
                "sale__seller",
                "sale__customer",
            )
            .prefetch_related(
                Prefetch(
                    "flights",
                    queryset=flights,
                    to_attr="prefetched_flights",
                )
            )
        )

        if request.user.role == User.Role.SELLER:
            reservations = reservations.filter(sale__seller=request.user)

        data = [self.serialize_reservation(r) for r in reservations]
        return Response({"success": True, "items": data})

    def post(self, request):
        data, error = self.validate_data(request.data, request.user)

        if error:
            return error

        sale_data = data["sale"]
        reservation_data = data["reservation"]
        flights = reservation_data.pop("flights")

        with transaction.atomic():
            sale = Sale.objects.create(**sale_data)

            reservation = Reservation.objects.create(
                sale=sale,
                **reservation_data,
            )

            reservation.flights.set(flights)

        return Response({
            "success": True,
            "message": "Reservation successfully registered.",
            "reservation_id": reservation.id,
            "sale_id": sale.id,
        })
