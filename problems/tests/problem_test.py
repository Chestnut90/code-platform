from django.test import TestCase

from .user_test import UserTestCase
from .category_test import CategoryModelTestCase, Category

from ..models import Problem, Answer, Commentary


class ProblemModelTestCase(TestCase):
    def setUp(self) -> None:
        UserTestCase().setUp()
        CategoryModelTestCase().setUp()

    # def test_default(self):
    #     problem = {
    #         "name": "problem1",
    #         "level": 1,
    #         "category": Category.objects.get(pk=1),
    #     }

    #     Problem.objects.create(**problem)
