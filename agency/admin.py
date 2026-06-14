from django.contrib import admin
from .models import Customer, Sale, Supplier, Reservation


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone"]
    search_fields = ["name", "email", "phone"]
    ordering = ["name"]


class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_id", "phone", "postal_code"]
    search_fields = ["name", "tax_id", "phone"]
    ordering = ["name"]


class SaleAdmin(admin.ModelAdmin):
    list_display = [
        "seller",
        "customer",
        "type",
        "payment",
        "amount_received",
        "cost",
        "sale_date",
    ]
    list_filter = [
        "payment",
        "type",
        "sale_date",
        "seller",
    ]
    search_fields = ["customer__name"]


class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        "locator",
        "passenger_count",
        "supplier",
        "issuer",
    ]
    list_filter = ["issuer", "supplier"]
    search_fields = ["locator"]


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Reservation, ReservationAdmin)
