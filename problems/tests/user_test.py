from django.contrib.auth.models import User
from django.test import TestCase


class UserTestCase(TestCase):

    _users = [
        {
            "username": "tommyhilfiger",
            "first_name": "hilfiger",
            "last_name": "tommy",
        },
        {
            "username": "numble",
            "first_name": "ble",
            "last_name": "num",
        },
        {
            "username": "codeplatform",
            "first_name": "code",
            "last_name": "platform",
        },
    ]

    def setUp(self) -> None:
        for user in self._users:
            User.objects.create(**user)

    def test_check(self):

        user0 = User.objects.get(pk=1)

        self.assertEqual(user0.last_name, "tommy")
