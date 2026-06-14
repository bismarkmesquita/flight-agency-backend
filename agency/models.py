from django.db import models
from core.models import BaseModel
from flights.models import Flight
from users.models import User
from sortedm2m.fields import SortedManyToManyField


class Customer(BaseModel):
    name = models.CharField(max_length=250)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        verbose_name="WhatsApp"
    )

    def __str__(self):
        return self.name


class Supplier(BaseModel):
    name = models.CharField(
        db_index=True,
        max_length=100,
    )
    tax_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )
    phone = models.CharField(max_length=20)

    # Address fields
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    neighborhood = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    address_number = models.CharField(max_length=100)
    complement = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.name}"


class Sale(BaseModel):
    class Type(models.TextChoices):
        B2C = "b2c", "B2C"
        B2B = "b2b", "B2B"

    class Payment(models.TextChoices):
        CREDIT_CARD = "credit_card", "Credit Card"
        DEBIT_CARD = "debit_card", "Debit Card"
        MONEY = "money", "Cash"
        TRANSFER = "transfer", "Transfer"
        TICKET = "ticket", "Ticket"

    seller = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
    )
    type = models.CharField(
        max_length=3,
        choices=Type.choices,
    )
    payment = models.CharField(
        max_length=20,
        choices=Payment.choices,
    )
    amount_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    sale_date = models.DateField(db_index=True)
    indication = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    @property
    def profit(self):
        return self.amount_received - self.cost

    def __str__(self):
        return f"{self.customer.name} - {self.sale_date}"


class Reservation(BaseModel):
    locator = models.CharField(
        max_length=20,
        unique=True,
    )
    sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
    )
    flights = SortedManyToManyField(
        Flight,
        related_name="reservations",
    )
    passenger_count = models.PositiveIntegerField()
    passengers = models.TextField(
        blank=True,
        null=True
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="reservations"
    )
    issuer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="reservations"
    )

    def __str__(self):
        return self.locator
