import os
from faker import Faker
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = "Populate local database with some data"
    faker = Faker()
    default_password = "agency"

    def handle(self, *args, **kwargs):
        cmd_start = timezone.now()

        if not settings.DEBUG or os.environ.get("DATABASE_URL"):
            print("This command can only be run in DEBUG mode")
            return

        self.now = timezone.now()
        self.today = self.now.date()

        User.objects.all().delete()

        self.gen_users()

        timetaken = timezone.now() - cmd_start
        print("\nPopulated in {} seconds.\n".format(timetaken.seconds))

    def gen_users(self):
        self.superuser = User.objects.create_superuser(
            email="agency@agency.com",
            password=self.default_password,
            name="Agency Admin",
            role=User.Role.ADMIN,
        )

        self.coordinator = User.objects.create_user(
            email="manager@agency.com",
            password=self.default_password,
            name="manager",
            role=User.Role.MANAGER,
        )

        self.seller = User.objects.create_user(
            email="seller@agency.com",
            password=self.default_password,
            name="Seller",
            role=User.Role.SELLER,
        )

        self.users = []
        for i in range(50):
            user = User(
                email=f"user{i}@user{i}.com",
                name=f"User {i}",
                role=User.Role.SELLER,
            )
            self.users.append(user)

        User.objects.bulk_create(self.users)

        print("USERS GENERATED")
