from django.urls import path
from agency.views.customers import CustomerView, CustomersView


urlpatterns = [
    path("customers/", CustomersView.as_view()),
    path("customers/<int:id>/", CustomerView.as_view()),
]
