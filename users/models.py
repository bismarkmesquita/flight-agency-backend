from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import BaseModel
from .managers import UserManager


class User(BaseModel, AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        MANAGER = "manager", _("Manager")
        SELLER = "seller", _("Seller")

    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    last_access = models.DateTimeField(blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.SELLER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.name} - {self.email}"


class InternalLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"

    created_at = models.DateTimeField(default=timezone.now)
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
    )
    entity = models.CharField(
        max_length=100,
        help_text="Model name. Ex: User, Sale, Reservation",
    )
    entity_id = models.PositiveIntegerField()
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    message = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.created_at:%Y-%m-%d %H:%M} - "
            f"{self.action} {self.entity}#{self.entity_id}"
        )
