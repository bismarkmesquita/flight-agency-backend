from faker import Faker
from knox.models import AuthToken
from users.models import User
from datetime import timedelta
from random import randint


def get_auth_header(
    role=User.Role.SELLER,
    access_level=User.AccessLevel.DEMO,
):
    user = User.objects.create_user(
        password="123456789",
        email=str(randint(0, 1000000000)) + "@test.com",
        role=role,
        access_level=access_level,
        name=Faker().name(),
    )

    token = AuthToken.objects.create(user, timedelta(days=1))[1]
    return {"Authorization": "Token " + token}, user
