from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch
from core.utils import get_object_or_none
from users.models import User
from flights.models import Flight
from agency.models import Reservation, Sale, Supplier
from agency.failures import CreateReservationFailureReason


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
            "supplier": self.serialize_user(reservation.supplier),
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

    def error_response(self, message, reason):
        return Response({
            "success": False,
            "message": message,
            "reason": reason,
        })

    def validate_data(self, data):
        required_fields = [
            "sale_id",
            "locator",
            "passengers",
            "passenger_count",
            "supplier_id",
            "issuer_id",
            "flight_ids",
        ]

        missing_fields = [
            field
            for field in required_fields
            if data.get(field) is None
        ]

        if missing_fields:
            return None, self.error_response(
                f"Campos obrigatórios: {', '.join(missing_fields)}",
                CreateReservationFailureReason.MISSING_FIELDS.value,
            )

        sale_id = data["sale_id"]
        locator = data["locator"]
        passenger_count = data["passenger_count"]
        supplier_id = data["supplier_id"]
        flight_ids = data["flight_ids"]
        issuer_id = data["issuer_id"]
        passengers = data["passengers"]

        # Validade sale
        sale = get_object_or_none(Sale, id=sale_id)
        if not sale:
            return None, self.error_response(
                "Sale not found.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        # Validade supplier
        supplier = get_object_or_none(Supplier, id=supplier_id)
        if not supplier:
            return None, self.error_response(
                "Supplier not found.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        # Validade issuer
        issuer = get_object_or_none(User, id=issuer_id)
        if not issuer:
            return None, self.error_response(
                "Issuer not found.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        # Validade locator
        if Reservation.objects.filter(locator=locator).exists():
            return None, self.error_response(
                "A reservation already exists with the provided locator number.",
                CreateReservationFailureReason.ALREADY_REGISTERED.value
            )

        # Validade flights
        flights = list(Flight.objects.filter(id__in=set(flight_ids)))
        if len(flights) != len(set(flight_ids)):
            return None, self.error_response(
                "One or more flights do not exist.",
                CreateReservationFailureReason.OBJECT_NOT_FOUND.value
            )

        return {
            "sale": sale,
            "issuer": issuer,
            "locator": locator,
            "supplier": supplier,
            "passengers": passengers,
            "passenger_count": passenger_count,
            "flights": flights,
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
        data, error = self.validate_data(request.data)

        if error:
            return error

        flights = data.pop("flights")

        with transaction.atomic():
            reservation = Reservation.objects.create(**data)
            reservation.flights.set(flights)

        return Response({
            "success": True,
            "message": "Reservation successfully registered.",
            "reservation_id": reservation.id,
        })
