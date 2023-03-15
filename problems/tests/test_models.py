from random import randint
from unittest import mock
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.db.utils import IntegrityError
from django.db.transaction import atomic
from django.conf import settings

from ..models import (
    Category,
    Problem,
    Answer,
    Commentary,
    Submission,
    Solution,
)


def create_user(username):
    return User.objects.create(username=username)


def create_n_users(n):
    for i in range(n):
        create_user(f"user_{i}")
    return User.objects.all()


class UserModelTestCase(TestCase):
    def setUp(self) -> None:
        create_n_users(3)

    def test_check(self):

        user0 = User.objects.get(pk=1)

        self.assertEqual(user0.username, "user_0")


def create_category(name):
    return Category.objects.create(name=name)


def create_n_categories(n):
    for i in range(n):
        create_category(f"category_{i}")


class CategoryModelTestCase(TestCase):
    def test_category(self):

        n = 3
        create_n_categories(n)
        self.assertEqual(Category.objects.count(), n)

        category0 = Category.objects.get(pk=1)

        self.assertEqual(category0.name, "category_0")

    def test_updated_created_time(self):

        settings.USE_TZ = False  # time warning.

        now = datetime.now()
        with mock.patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = now
            name = "category_time"
            create_category(name)
            category = Category.objects.get(name=name)

        self.assertEqual(category.updated_at, now)
        self.assertEqual(category.created_at, now)

        settings.USE_TZ = True


def create_problem(**kwargs):

    _answer = kwargs.pop("answer")
    _commentary = kwargs.pop("commentary")

    with atomic():
        kwargs["answer"] = Answer.objects.create(answer=_answer)
        kwargs["commentary"] = Commentary.objects.create(comment=_commentary)

        problem = Problem.objects.create(**kwargs)
    return problem


def create_n_problem(n, users, categories):

    user_len = users.count()
    categories_lens = categories.count()

    for i in range(n):
        problem = {
            "name": f"name-{i}",
            "answer": f"answer-{i}",
            "commentary": f"comment-{i}",
            "description": f"description-{i}",
            "level": randint(1, 5),
            "owner": users[randint(0, user_len - 1)],
            "category": categories[randint(0, categories_lens - 1)],
        }
        create_problem(**problem)


class ProblemModelTestCase(TestCase):
    """
    create problem-answer-commentary
    """

    def setUp(self) -> None:

        create_n_users(3)
        create_n_categories(3)
        create_n_problem(3, User.objects.all(), Category.objects.all())

    def test_default(self):

        kwargs = {
            "name": "default_problem",
            "level": 1,
            "description": "default_problem_description",
            "answer": "answer",
            "commentary": "comment",
            "owner": User.objects.get(pk=1),
            "category": Category.objects.get(pk=1),
        }
        problem = create_problem(**kwargs)
        instance = Problem.objects.get(pk=problem.pk)

        self.assertEqual(instance.name, problem.name)
        self.assertEqual(instance.level, problem.level)
        self.assertEqual(instance.description, problem.description)
        self.assertEqual(instance.category, problem.category)
        self.assertEqual(instance.answer, problem.answer)
        self.assertEqual(instance.commentary, problem.commentary)
        self.assertEqual(instance.owner, problem.owner)

    def test_problem_answer_commentary_one_to_one(self):

        problems_count = Problem.objects.count()
        answers_count = Answer.objects.count()
        commentaries_count = Commentary.objects.count()

        self.assertTrue(
            problems_count == answers_count and problems_count == commentaries_count
        )

        # create problem with first_answer
        first_answer = Answer.objects.get(pk=1)
        with self.assertRaises(IntegrityError):
            with atomic():
                problem = {
                    "name": "one_to_one_test",
                    "level": 1,
                    "owner": User.objects.get(pk=1),
                    "answer": first_answer,
                    "commentary": Commentary.objects.create(comment="one_to_one_test"),
                    "description": "--",
                    "category": Category.objects.get(pk=1),
                }
                Problem.objects.create(**problem)

        # still same count
        problems_count = Problem.objects.count()
        answers_count = Answer.objects.count()
        commentaries_count = Commentary.objects.count()

        self.assertTrue(
            problems_count == answers_count and problems_count == commentaries_count
        )

        # create problem with first_commentary
        first_commentary = Commentary.objects.get(pk=1)
        with self.assertRaises(IntegrityError):
            with atomic():
                problem = {
                    "name": "one_to_one_test",
                    "level": 1,
                    "owner": User.objects.get(pk=1),
                    "answer": Answer.objects.create(answer="one_to_one_test"),
                    "commentary": first_commentary,
                    "description": "--",
                    "category": Category.objects.get(pk=1),
                }
                Problem.objects.create(**problem)

        # still same count
        problems_count = Problem.objects.count()
        answers_count = Answer.objects.count()
        commentaries_count = Commentary.objects.count()

        self.assertTrue(
            problems_count == answers_count and problems_count == commentaries_count
        )

    def test_delete_answer_and_commentary(self):
        """
        test on_delete=PROTECT, delete answer and commentary related problem
        """
        from django.db.models.deletion import ProtectedError

        # delete answer and commentary before problem deletion.
        problem = Problem.objects.get(pk=1)

        answer = problem.answer
        with self.assertRaises(ProtectedError):
            answer.delete()

        commentary = problem.commentary
        with self.assertRaises(ProtectedError):
            commentary.delete()

        # delete answer and commentary after problem deletion
        problem.delete()
        answer.delete()
        commentary.delete()

        with self.assertRaises(Problem.DoesNotExist):
            problem = Problem.objects.get(pk=1)

    def test_name_unique_constraints(self):

        first_problem = Problem.objects.first()
        prev_n = Problem.objects.count()

        with self.assertRaises(IntegrityError):
            with atomic():
                create_problem(
                    **{
                        "name": first_problem.name,
                        "answer": "name_unique_constraints",
                        "commentary": "name_unique_constraints",
                        "level": 1,
                        "owner": User.objects.first(),
                        "category": Category.objects.first(),
                    }
                )

        after_n = Problem.objects.count()

        self.assertEqual(prev_n, after_n)  # problem not created.

    def test_level_check_constratins(self):
        """test level constraints"""

        with self.assertRaises(IntegrityError):
            with atomic():
                problem = {
                    "name": "level_0",
                    "level": 0,
                    "description": "--",
                    "category": Category.objects.get(pk=1),
                    "answer": "answer-level0",
                    "commentary": "comment-level0",
                    "owner": User.objects.get(pk=1),
                }
                create_problem(**problem)

    def test_owner_cascade(self):
        """
        test CASCADE, owner foreignkey on_delete option.
        """

        # find problem owner
        for user in User.objects.all():
            if user.own_problems.count() > 0:
                break

        n = Problem.objects.count()
        user_problems_count = Problem.objects.filter(owner=user).count()

        # delete user
        user.delete()
        problems = Problem.objects.filter(owner=user)

        self.assertFalse(problems.exists())  # expect false
        self.assertEqual(Problem.objects.count(), n - user_problems_count)

    def test_category_set_null(self):

        # get first problem
        default_problem = Problem.objects.get(pk=1)
        category = default_problem.category

        # delete category and re-fetch
        category.delete()
        updated_problem = Problem.objects.get(pk=1)

        self.assertEqual(updated_problem.category, None)


def create_submission(user, problem, **kwargs):

    return Submission.objects.create(user=user, problem=problem, **kwargs)


def create_n_submission(n, users, problems):
    import itertools

    users_count = users.count()
    problems_count = problems.count()
    max_n = users_count * problems_count
    n = max_n if n > max_n else n

    product = list(itertools.product(range(users_count), range(problems_count)))
    for i in range(n):
        index = randint(0, len(product) - 1)
        pair = product.pop(index)
        create_submission(users[pair[0]], problems[pair[1]])


class SubmissionModelTestCase(TestCase):
    def setUp(self) -> None:
        create_n_users(3)
        create_n_categories(1)
        create_n_problem(3, User.objects.all(), Category.objects.all())
        create_n_submission(3, User.objects.all(), Problem.objects.all())

    def test_default(self):

        # prev count
        n = Submission.objects.count()

        # add user
        user = create_user("hello")
        first_problem = Problem.objects.first()

        submission = create_submission(user, first_problem)

        self.assertEqual(submission.user, user)
        self.assertEqual(submission.problem, first_problem)
        self.assertEqual(Submission.objects.count(), n + 1)

    def test_unique_user_problem(self):

        first_submission = Submission.objects.first()

        user = first_submission.user
        problem = first_submission.problem

        with self.assertRaises(IntegrityError):
            with atomic():
                create_submission(user, problem)

        self.assertEqual(
            Submission.objects.filter(user=user, problem=problem).count(), 1
        )

    def test_score_constraints(self):

        # prev count
        prev_n = Submission.objects.count()

        # add user
        user = create_user("hello")
        first_problem = Problem.objects.first()

        with self.assertRaises(IntegrityError):
            with atomic():
                submission = create_submission(user, first_problem, **{"score": 101})

        with self.assertRaises(IntegrityError):
            with atomic():
                submission = create_submission(user, first_problem, **{"score": -1})

        self.assertEqual(prev_n, Submission.objects.count())


def create_solution(user, problem, answer):
    try:
        submission = Submission.objects.find_submission_on_problem(problem.id, user)
    except Submission.DoesNotExist:
        submission = create_submission(user, problem)

    return Solution.objects.create(submission, answer)


def create_n_solution(n, user, problem, answer):
    raise NotImplementedError()


class SolutionModelTestCase(TestCase):
    def setUp(self) -> None:
        create_n_users(3)
        create_n_categories(2)
        create_n_problem(2, User.objects.all(), Category.objects.all())

    def test_default(self):

        first_problem = Problem.objects.first()
        first_user = User.objects.first()

        submission = create_submission(first_user, first_problem)

        prev_n = submission.solutions.count()

        # submit first solution
        solution = Solution.objects.create(
            **{"answer": "answer", "submission": submission}
        )

        n = submission.solutions.count()

        self.assertEqual(prev_n, 0)
        self.assertEqual(prev_n + 1, n)
        self.assertEqual("answer", Solution.objects.get(answer="answer").answer)

        # submit second solution
        prev_n = n
        solution = Solution.objects.create(
            **{"answer": "answer2", "submission": submission}
        )

        n = submission.solutions.count()
        self.assertEqual(prev_n, 1)
        self.assertEqual(prev_n + 1, n)
        self.assertEqual("answer2", Solution.objects.get(answer="answer2").answer)
