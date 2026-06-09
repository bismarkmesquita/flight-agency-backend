from faker import Faker
from knox.models import AuthToken
from users.models import User
from datetime import timedelta
from random import randint


def get_auth_header(
    role=User.Role.SELLER,
):
    user = User.objects.create_user(
        password="123456789",
        email=str(randint(0, 1000000000)) + "@test.com",
        role=role,
        name=Faker().name(),
    )

    token = AuthToken.objects.create(user, timedelta(days=1))[1]
    return {"Authorization": "Token " + token}, user
