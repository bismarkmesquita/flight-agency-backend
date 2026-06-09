from django.test import TestCase
from faker import Faker
from django.conf import settings
import logging


class BaseTestCase(TestCase):
    def setUp(self) -> None:
        settings.DEBUG = True

        self.fake = Faker()

        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
