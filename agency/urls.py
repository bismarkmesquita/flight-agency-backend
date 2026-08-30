from django.urls import path
from agency.views.customers import CustomerView, CustomersView
from agency.views.reservations import ReservationsView
from agency.views.suppliers import CreateSupplierView, SupplierView, SuppliersView
from agency.views.dashboard import DashboardView


urlpatterns = [
    path("customers/", CustomersView.as_view()),
    path("customers/<int:id>/", CustomerView.as_view()),
    path("reservations/", ReservationsView.as_view()),
    path("suppliers/", SuppliersView.as_view()),
    path("suppliers/create/", CreateSupplierView.as_view()),
    path("suppliers/<int:id>/", SupplierView.as_view()),
    path("dashboard/", DashboardView.as_view()),
]
