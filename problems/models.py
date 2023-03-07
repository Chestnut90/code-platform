from django.db import models
from django.contrib.auth.models import User

from .models_abstract import AutoTimeTrackingModelBase

CATEGORY_DEFAULT_VALUE = "None"


class Answer(AutoTimeTrackingModelBase):
    """Problem answer model, submit by problem owner"""

    answer = models.TextField()

    def __str__(self) -> str:
        return f"answer of {self.problem}" if hasattr(self, "problem") else "deleted"


class Commentary(AutoTimeTrackingModelBase):
    """Problem Commentary model, submit by problem owner"""

    comment = models.TextField()

    def __str__(self) -> str:
        return f"comment of {self.problem}" if hasattr(self, "problem") else "deleted"


class Category(AutoTimeTrackingModelBase):
    """problem category model definition"""

    category = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        default=CATEGORY_DEFAULT_VALUE,
    )

    def __str__(self) -> str:
        return f"{self.category}"


class Problem(AutoTimeTrackingModelBase):

    """Problem model definition"""

    # name of this problem.
    name = models.CharField(max_length=50)
    # check 1 to 5
    level = models.PositiveSmallIntegerField()
    # string about problem
    description = models.TextField()

    # TODO : use choice?
    # using bfs, dfs, stack...
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_DEFAULT,
        related_name="problems",
        default=CATEGORY_DEFAULT_VALUE,  # TODO : error when category deleted.
    )

    commentary = models.OneToOneField(
        "Commentary",
        on_delete=models.PROTECT,
        related_name="problem",
    )
    answer = models.OneToOneField(
        "Answer",
        on_delete=models.PROTECT,
        related_name="problem",
    )

    # owner of problem
    owner = models.ForeignKey(
        User,  # default auth user model.
        on_delete=models.CASCADE,
        related_name="own_problems",
    )

    def submitted_count(self):
        return self.submissions.all().count()

    def __str__(self) -> str:
        return f"{self.name}"
