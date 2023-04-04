from django.db.models import Q
from django.urls import reverse, resolve
from rest_framework.test import APITestCase, APIRequestFactory, APIClient

from ..models import User, Problem, Category, Answer, Commentary

from . import test_models

factory = APIRequestFactory()


class ProblemsAPITestCase(APITestCase):

    client = APIClient(enforce_csrf_checks=True)
    user_count = 3
    category_count = 2
    problem_count = 10
    url = "/problems/"

    def setUp(self) -> None:

        test_models.create_n_categories(self.category_count)
        test_models.create_n_users(self.user_count)
        test_models.create_n_problem(
            self.problem_count, User.objects.all(), Category.objects.all()
        )

        return super().setUp()

    def test_get_default(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        json = response.json()
        self.assertEqual(json["count"], self.problem_count)

    def test_get_with_queries(self):
        """
        test queries, levels= & categories=
        not test pagination, use rest_framework default pagination class
        """

        # queries level with 0
        response = self.client.get(f"{self.url}?levels=0")

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json["count"], Problem.objects.filter(level=0).count())

        # queries levels with 1, 2
        response = self.client.get(f"{self.url}?levels=1, 2")

        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(
            json["count"], Problem.objects.filter(Q(level=1) | Q(level=2)).count()
        )

        # queries levels with 1, 2 and categories with id 1
        response = self.client.get(f"{self.url}?levels=1, 2&categories=1")

        self.assertEqual(response.status_code, 200)
        json = response.json()
        print("json : ", json)
        problems = Problem.objects.filter(
            (Q(level=1) | Q(level=2)) & Q(category=1),
        )
        for problem in problems:
            print(
                "problem. level={}, category={}".format(problem.level, problem.category)
            )

        self.assertEqual(json["count"], problems.count())

        # queries levels with 1, 2 and categories with id 1, 2
        response = self.client.get(f"{self.url}?levels=1, 2&categories=1,2")

        self.assertEqual(response.status_code, 200)
        json = response.json()
        problems = Problem.objects.filter(
            (Q(level=1) | Q(level=2)) & (Q(category=1) | Q(category=2)),
        )
        self.assertEqual(json["count"], problems.count())

        # queries levels and categories empty
        response = self.client.get(f"{self.url}?levels=&categories=")

        self.assertEqual(response.status_code, 200)
        json = response.json()
        problems = Problem.objects.filter()
        self.assertEqual(json["count"], problems.count())

    def test_post_default(self):

        name = "post-default"
        prev_n = Problem.objects.count()

        user_logged_in = User.objects.first()
        self.client.force_login(user_logged_in)
        response = self.client.post(
            self.url,
            data={
                "name": name,
                "level": 1,
                "category": 1,
                "description": name,
                "answer": {"answer": name},
                "commentary": {"comment": name},
            },
            format="json",
        )
        # check response status code
        self.assertEqual(response.status_code, 201)

        problem = Problem.objects.get(name=name)
        # check problems count after post
        self.assertEqual(prev_n + 1, Problem.objects.count())
        # check created problem name with post data name
        self.assertEqual(name, problem.name)
        # check equals request user with problem owner
        self.assertEqual(user_logged_in, problem.owner)

    def test_post_missing_values(self):
        # TODO : ???
        name = "post-default"
        prev_n = Problem.objects.count()

        user_logged_in = User.objects.first()
        self.client.force_login(user_logged_in)
        response = self.client.post(
            self.url,
            data={  # required fileds
                "name": name,
                "level": 1,
                "category": 1,
                "description": name,
                # "answer": {"answer": name},
                "commentary": {"comment": name},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(prev_n, Problem.objects.count())


class ProblemAPITestCase(APITestCase):
    """Problem api test"""

    client = APIClient(enforce_csrf_checks=True)
    user_count = 3
    category_count = 2
    problem_count = 10
    url = classmethod(lambda self, id: f"/problems/{id}")

    def setUp(self) -> None:

        test_models.create_n_categories(self.category_count)
        test_models.create_n_users(self.user_count)
        test_models.create_n_problem(
            self.problem_count, User.objects.all(), Category.objects.all()
        )

    def test_get_default(self):

        first_problem = Problem.objects.get(pk=1)

        response = self.client.get(self.url(first_problem.pk))

        self.assertEqual(response.status_code, 200)

        json = response.json()
        self.assertEqual(first_problem.id, json["id"])
        self.assertEqual(first_problem.name, json["name"])
        self.assertEqual(first_problem.category.name, json["category"])
        self.assertEqual(first_problem.level, json["level"])

    def test_put_default(self):

        first_problem = Problem.objects.first()
        user_logged_in = first_problem.owner
        self.client.force_login(user_logged_in)

        # put
        name = "put-data"
        self.problem_data = {
            "name": name,
            "level": 1,
            "category": 1,
            "answer": {"answer": name},
            "commentary": {"comment": name},
            "description": name,
        }

        response = self.client.put(
            self.url(first_problem.pk), data=self.problem_data, format="json"
        )

        self.assertEqual(response.status_code, 200)

        problem = Problem.objects.get(pk=first_problem.pk)
        self.assertEqual(problem.name, name)
        self.assertEqual(problem.answer.answer, name)
        self.assertEqual(problem.commentary.comment, name)

    def test_patch_default(self):
        # TODO : patch can update model with partial data.
        pass


class SolutionAPITestCase(APITestCase):

    url = lambda self, id: f"/problems/{id}/solutions"
    pass
