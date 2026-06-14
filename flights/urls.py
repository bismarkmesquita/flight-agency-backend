from django.urls import path
from .views import CreateFlightView


urlpatterns = [
    path("create-flight/", CreateFlightView.as_view(), name="create-flight"),
]
