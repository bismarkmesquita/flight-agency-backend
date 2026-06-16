from django.db import models
from core.models import BaseModel
from rest_framework.validators import ValidationError


class Airline(BaseModel):
    name = models.CharField(max_length=100)
    iata = models.CharField(
        unique=True,
        max_length=3,
        help_text="Ex: LA, G3, etc."
    )

    def __str__(self):
        return f"{self.name} - {self.iata}"


class Airport(BaseModel):
    iata = models.CharField(
        max_length=3,
        unique=True,
        db_index=True
    )
    icao = models.CharField(
        max_length=4,
        unique=True,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.iata} - {self.city}"


class Flight(BaseModel):
    flight_number = models.CharField(max_length=4)
    airline = models.ForeignKey(
        Airline,
        on_delete=models.PROTECT,
    )
    departure_date = models.DateTimeField(db_index=True)
    arrival_date = models.DateTimeField()
    departure_airport = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="departures",
    )
    arrival_airport = models.ForeignKey(
        Airport,
        on_delete=models.PROTECT,
        related_name="arrivals",
    )

    @property
    def iata(self):
        return f"{self.airline.iata}{self.flight_number}"

    def __str__(self):
        return self.iata

    def clean(self):
        if self.arrival_date <= self.departure_date:
            raise ValidationError(
                "Arrival date must be after departure date."
            )

        if self.departure_airport == self.arrival_airport:
            raise ValidationError(
                "Departure and arrival airports must be different."
            )

    class Meta:
        unique_together = ('flight_number', 'airline', 'departure_date')
        indexes = [
            models.Index(fields=["flight_number", "departure_date"]),
        ]
