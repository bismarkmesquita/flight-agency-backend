from django.urls import path
from agency.views.customers import CustomerView, CustomersView
from agency.views.reservation import ReservationsView
from agency.views.sales import SalesView
from agency.views.suppliers import CreateSupplierView, SupplierView, SuppliersView


urlpatterns = [
    path("customers/", CustomersView.as_view()),
    path("customers/<int:id>/", CustomerView.as_view()),
    path("reservations/", ReservationsView.as_view()),
    path("sales/", SalesView.as_view()),
    path("suppliers/", SuppliersView.as_view()),
    path("suppliers/create/", CreateSupplierView.as_view()),
    path("suppliers/<int:id>/", SupplierView.as_view()),
]
