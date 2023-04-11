from time import sleep

from django.db import models
from django.db.models import QuerySet, Count, Q

# from django.db.models.query import _BaseQuerySet
from django.db.models.manager import BaseManager
from django.conf import settings

# for hint
from typing import Any, TypeVar

from config import redis  # custom redis interface


_T = TypeVar("_T", bound=models.Model)
_QS = TypeVar("_QS", bound="_BaseQuerySet[Any]")


def update_problem_cache(obj):
    """update cache if object is related model with problem"""
    if not hasattr(obj, "problem"):
        return

    pk = obj.problem.pk
    key = PROBLEM_KEY.format(pk)

    hit = redis.get(key)
    if hit:
        # update cache
        redis.set(key, obj.problem)


class DelayQuerySet(QuerySet):
    def get(self, *args, **kwargs):
        """override method, to force time dealy"""
        print("delay queryset get called")
        sleep(settings.DEBUG_PROBLEM_QUERY_DELAY)
        return super().get(*args, **kwargs)

    def filter(self: _QS, *args: Any, **kwargs: Any) -> _QS:
        """override method, to force time delay"""
        print("delay queryset filter called")
        sleep(settings.DEBUG_PROBLEM_QUERY_DELAY)
        return super().filter(*args, **kwargs)


class DelayManager(models.Manager):
    def get(self, *args, **kwargs):
        """override method, to force time dealy"""
        # print("delay manager get called")
        # sleep(settings.DEBUG_PROBLEM_QUERY_DELAY)
        return super().get(*args, **kwargs)

    def filter(self: _QS, *args: Any, **kwargs: Any) -> _QS:
        """override method, to force time delay"""
        # print("delay manager filter called")
        # sleep(settings.DEBUG_PROBLEM_QUERY_DELAY)
        return super().filter(*args, **kwargs)


SEPARATOR = ","

# use .format()
PROBLEM_KEY = "problems.{}"


class ProblemManager(DelayManager):
    """
    Problem model manager
    do queries.
    """

    def get_cached_queryset(self, levels=str, categories=str):
        """cached"""

        def _list_queries(field_name, values: list) -> models.Q:
            query = models.Q()
            for value in values:
                query |= models.Q(**{field_name: value})
            return query

        assert isinstance(levels, str) or isinstance(
            categories, str
        ), "pass comma separated value"

        # TODO : unique key, sort levels value when not sorted.
        key = PROBLEM_KEY.format(f"levels={levels}.categories={categories}")

        hit = redis.get(key)
        if not hit:
            # TODO : error fix
            query = models.Q()
            if levels:
                query &= models.Q(_list_queries("level", levels.split(SEPARATOR)))
            if categories:
                query &= _list_queries("category", categories.split(SEPARATOR))
            # TODO : query with rate of solved

            hit = (
                self.prefetch_related("submissions")
                .select_related("category", "owner")
                .filter(query)
            )
            redis.set(key, hit)

        return hit

    def get_cached_problem(self, id):
        """
        get problem using cache, 'look aside'
        """
        key = PROBLEM_KEY.format(id)
        hit = redis.get(key)

        if not hit:
            hit = self.get(pk=id)
            redis.set(key, hit)

        return hit

    def check_answer(self, problem_id, answer):
        """
        check problem answer with given answer.\n
        can raise Problem.DoesNotExist
        """
        problem = self.get(pk=problem_id)

        return 100 if problem.answer.answer == answer else 0


class SubmissionManager(models.Manager):
    def find_submission_on_problem(self, problem_id, user):
        """
        find submission instance with problem_id and user object
        can raise Submission.DoesNotFound
        """
        return self.get(models.Q(problem=problem_id) & models.Q(user=user.id))


class SolutionManager(models.Manager):
    def find_submitted_solutions(self, problem_id, user):
        """
        find solutions of problem which user submitted.
        ordered by lastest submitted solutions.
        """
        try:
            from django.apps import apps

            submission_model = apps.get_model("problems", "Submission")
            submission = submission_model.objects.find_submission_on_problem(
                problem_id, user
            )
        except submission_model.DoesNotExist:  # catch DoesNotExist
            raise self.model.DoesNotExist

        return self.filter(submission=submission).order_by("-created_at")
