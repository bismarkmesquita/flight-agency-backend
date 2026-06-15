from django.urls import path
from .views import AirlinesView, AirportsView, FlightView, NextFlightsView


urlpatterns = [
    path("airlines/", AirlinesView.as_view()),
    path("airports/", AirportsView.as_view()),
    path("", FlightView.as_view()),
    path("next/", NextFlightsView.as_view()),
]
