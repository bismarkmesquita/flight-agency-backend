import re
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Prefetch
from django.utils.dateparse import parse_datetime
from agency.models import Reservation
from .models import Airline, Airport, Flight
from .failures import CreateFlightFailureReason


class AirlinesView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        airlines = Airline.objects.all()
        data = [self.serializer(airline) for airline in airlines]

        return Response({"success": True, "airlines": data})

    def serializer(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "iata": obj.iata,
        }


class AirportsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        airports = Airport.objects.all()
        data = [self.serializer(airline) for airline in airports]

        return Response({"success": True, "airports": data})

    def serializer(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "iata": obj.iata,
            "icao": obj.icao,
            "city": obj.city,
            "country": obj.country,
        }


class NextFlightsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        reservations_qs = (
            Reservation.objects
            .select_related(
                "sale",
                "sale__customer",
            )
        )

        now = timezone.now()

        flights = (
            Flight.objects.filter(departure_date__gte=now)
            .select_related(
                "airline",
                "departure_airport",
                "arrival_airport"
            )
            .prefetch_related(
                Prefetch(
                    "reservations",
                    queryset=reservations_qs,
                    to_attr="prefetched_reservations",
                ),
            )
            .order_by("departure_date")[:15]
        )
        data = [self.serialize_flight(flight) for flight in flights]

        return Response({"success": True, "flights": data})

    def serialize_reservation(self, obj):
        return {
            "locator": obj.locator,
            "name": obj.sale.customer.name,
            "phone": obj.sale.customer.phone or None,
        }

    def serialize_flight(self, obj):
        return {
            "id": obj.id,
            "iata": obj.iata,
            "airline": {
                "id": obj.airline.id,
                "iata": obj.airline.iata
            },
            "departure_date": timezone.localtime(obj.departure_date).isoformat(),
            "arrival_date": timezone.localtime(obj.arrival_date).isoformat(),
            "departure_airport": {
                "id": obj.departure_airport.id,
                "iata": obj.departure_airport.iata,
                "city": obj.departure_airport.city,
            },
            "arrival_airport": {
                "id": obj.arrival_airport.id,
                "iata": obj.arrival_airport.iata,
                "city": obj.arrival_airport.city,
            },
            "reservations": [
                self.serialize_reservation(reservation)
                for reservation in obj.prefetched_reservations
            ]
        }


class FlightView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        data = request.data

        required_fields = [
            "flight_number",
            "airline_id",
            "departure_airport_id",
            "arrival_airport_id",
            "departure_date",
            "arrival_date"
        ]
        missing_fields = [
            field for field in required_fields if not data.get(field)
        ]
        if missing_fields:
            return Response(
                {
                    "success": False,
                    "message": f"Required fields: {', '.join(missing_fields)}",
                    "reason": CreateFlightFailureReason.MISSING_FIELDS.value,
                }
            )

        flight_number = data["flight_number"]
        airline_id = data["airline_id"]
        departure_airport_id = data["departure_airport_id"]
        arrival_airport_id = data["arrival_airport_id"]

        parsed_departure_date = parse_datetime(data.get("departure_date"))
        parsed_arrival_date = parse_datetime(data.get("arrival_date"))

        if not re.match(r"^\d{1,4}$", str(flight_number)):
            return Response(
                {
                    "success": False,
                    "message": "Invalid flight number.",
                    "reason": CreateFlightFailureReason.INVALID_FLIGHT_NUMBER.value,
                }
            )

        if departure_airport_id == arrival_airport_id:
            return Response(
                {
                    "success": False,
                    "message": "Choose different airports.",
                    "reason": CreateFlightFailureReason.INVALID_AIRPORT.value,
                }
            )

        if not parsed_arrival_date or not parsed_departure_date:
            return Response(
                {
                    "success": False,
                    "message": "Invalid dates.",
                    "reason": CreateFlightFailureReason.INVALID_DATE.value
                }
            )

        if timezone.is_naive(parsed_departure_date):
            parsed_departure_date = timezone.make_aware(parsed_departure_date)

        if timezone.is_naive(parsed_arrival_date):
            parsed_arrival_date = timezone.make_aware(parsed_arrival_date)

        if parsed_arrival_date <= parsed_departure_date:
            return Response(
                {
                    "success": False,
                    "message": "Arrival date must be after departure date.",
                    "reason": CreateFlightFailureReason.INVALID_DATE.value,
                }
            )

        try:
            airline = Airline.objects.get(id=airline_id)
        except Airline.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Airline not found.",
                    "reason": CreateFlightFailureReason.INVALID_AIRLINE.value,
                }
            )

        try:
            departure_airport = Airport.objects.get(id=departure_airport_id)
            arrival_airport = Airport.objects.get(id=arrival_airport_id)
        except Airport.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Invalid airport.",
                    "reason": CreateFlightFailureReason.INVALID_AIRPORT.value,
                }
            )

        existing_flight = Flight.objects.filter(
            flight_number=flight_number,
            airline=airline,
            departure_date=parsed_departure_date,
        ).exists()

        if existing_flight:
            return Response(
                {
                    "success": False,
                    "message": "There is already a flight with the IATA code and dates provided.",
                    "reason": CreateFlightFailureReason.ALREADY_REGISTERED.value
                }
            )

        flight = Flight.objects.create(
            airline=airline,
            flight_number=flight_number,
            departure_date=parsed_departure_date,
            arrival_date=parsed_arrival_date,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
        )

        return Response({
            "success": True,
            "message": "Flight successfully registered.",
            "flight": self.serializer(flight, departure_airport, arrival_airport),
        })

    def serializer(self, flight, departure_airport, arrival_airport):
        return {
            "id": flight.id,
            "iata": flight.iata,
            "airline": {
                "id": flight.airline.id,
                "name": flight.airline.name
            },
            "departure_date": timezone.localtime(flight.departure_date).isoformat(),
            "arrival_date": timezone.localtime(flight.arrival_date).isoformat(),
            "departure_airport": {
                "id": departure_airport.id,
                "iata": departure_airport.iata,
                "city": departure_airport.city,
            },
            "arrival_airport": {
                "id": arrival_airport.id,
                "iata": arrival_airport.iata,
                "city": arrival_airport.city,
            },
        }
