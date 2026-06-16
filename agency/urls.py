from django.urls import path
from agency.views.customers import CustomerView, CustomersView
from agency.views.reservation import ReservationsView
from agency.views.sales import SalesView


urlpatterns = [
    path("customers/", CustomersView.as_view()),
    path("customers/<int:id>/", CustomerView.as_view()),
    path("reservations/", ReservationsView.as_view()),
    path("sales/", SalesView.as_view()),
]
