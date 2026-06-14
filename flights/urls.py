from django.urls import path
from .views import CreateFlightView, GetAirlinesView, GetAirportsView


urlpatterns = [
    path("airlines/", GetAirlinesView.as_view(), name="get-airlines"),
    path("airports/", GetAirportsView.as_view(), name="get-airports"),
    path("create-flight/", CreateFlightView.as_view(), name="create-flight"),
]
