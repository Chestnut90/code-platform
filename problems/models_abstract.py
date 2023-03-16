from time import sleep

from django.db import models
from django.db.models import QuerySet

# from django.db.models.query import _BaseQuerySet
from django.db.models.manager import BaseManager
from django.conf import settings


# for hint
from typing import Any, TypeVar

_T = TypeVar("_T", bound=models.Model)
_QS = TypeVar("_QS", bound="_BaseQuerySet[Any]")


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


class DelayManager(BaseManager.from_queryset(QuerySet)):
    def get(self, *args, **kwargs):
        """override method, to force time dealy"""
        # print("delay manager get called")
        sleep(settings.DEBUG_PROBLEM_QUERY_DELAY)
        return super().get(*args, **kwargs)

    def filter(self: _QS, *args: Any, **kwargs: Any) -> _QS:
        """override method, to force time delay"""
        # print("delay manager filter called")
        sleep(settings.DEBUG_PROBLEM_QUERY_DELAY)
        return super().filter(*args, **kwargs)


class AutoTimeTrackingModelBase(models.Model):
    """Abstract class for creation time and updated time"""

    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AnswerModelBase(AutoTimeTrackingModelBase):
    """Abstract class for answer message"""

    class Meta:
        abstract = True

    answer = models.TextField()


class ScoreModelBase(models.Model):
    """Abstract class for holding score field"""

    class Meta:
        abstract = True
        # constraints = [
        #     models.CheckConstraint(
        #         check=models.Q(score=0) | models.Q(score=100),
        #         name="score_zero_or_hundred",
        #     ),
        # ]

    score = models.PositiveSmallIntegerField(default=0)

    @staticmethod
    def get_score_constraints(table: str):
        return models.CheckConstraint(
            check=models.Q(score=0) | models.Q(score=100),
            name=f"score_zero_or_hundred_{table}",
        )
