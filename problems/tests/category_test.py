from django.test import TestCase

from ..models import Category


class CategoryModelTestCase(TestCase):

    categories = [
        {"category": "bfs"},
        {"category": "dfs"},
        {"category": "basic"},
    ]

    def setUp(self) -> None:
        for category in self.categories:
            Category.objects.create(**category)

    def test_category(self):
        print(Category.objects.all())
