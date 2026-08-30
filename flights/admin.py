from django.contrib import admin
from flights.models import Airline, Airport, Flight


class AirlineAdmin(admin.ModelAdmin):
    list_display = ["name", "iata"]
    search_fields = ["name", "iata"]
    ordering = ["name"]


class AirportAdmin(admin.ModelAdmin):
    list_display = ["iata", "icao", "name"]
    search_fields = ["iata", "icao", "name"]


class FlightAdmin(admin.ModelAdmin):
    list_display = ["flight_number", "airline", "departure_date", "arrival_date"]
    list_filter = ["airline"]
    search_fields = ["flight_number", "airline__name"]
    ordering = ["-departure_date"]


admin.site.register(Airline, AirlineAdmin)
admin.site.register(Airport, AirportAdmin)
admin.site.register(Flight, FlightAdmin)
