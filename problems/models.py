from django.db import models
from django.contrib.auth.models import User

from .models_abstract import (
    AutoTimeTrackingModelBase,
    AnswerModelBase,
    ScoreModelBase,
)


class Answer(AnswerModelBase):
    """Problem answer model, submit by problem owner"""

    def __str__(self) -> str:
        return f"answer of {self.problem}" if hasattr(self, "problem") else "deleted"


class Commentary(AutoTimeTrackingModelBase):
    """Problem Commentary model, submit by problem owner"""

    comment = models.TextField()

    def __str__(self) -> str:
        return f"comment of {self.problem}" if hasattr(self, "problem") else "deleted"


class Category(AutoTimeTrackingModelBase):
    """Category of Problem model definition"""

    category = models.CharField(
        max_length=50,
        unique=True,
    )

    def __str__(self) -> str:
        return f"{self.category}"


class Problem(AutoTimeTrackingModelBase):
    """Problem model definition"""

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(level__gte=1, level__lte=5), name="level_range"
            ),
        ]

    # name of this problem.
    name = models.CharField(max_length=50)
    # problem level (1 to 5)
    level = models.PositiveSmallIntegerField()
    # string about problem
    description = models.TextField()
    # TODO : error when category deleted.
    # using bfs, dfs, stack...
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        related_name="problems",
    )
    # commentary relation
    commentary = models.OneToOneField(
        "Commentary",
        on_delete=models.PROTECT,
        related_name="problem",
    )
    # answer relation
    answer = models.OneToOneField(
        "Answer",
        on_delete=models.PROTECT,
        related_name="problem",
    )
    # owner relation
    owner = models.ForeignKey(
        User,  # default auth user model.
        on_delete=models.CASCADE,
        related_name="own_problems",
    )

    def submitted_count(self):
        return self.submissions.all().count()

    def __str__(self) -> str:
        return f"{self.name}"


class Submission(
    AutoTimeTrackingModelBase,
    ScoreModelBase,
):
    """
    Submission Model definition,
    (user, problem) : submission => (1 : 1)
    """

    class Meta(ScoreModelBase.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["user", "problem"],
                name="unique_user_problem",
            ),
            ScoreModelBase.get_score_constraints("submission"),
        ]

    # user who submit
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    # which problem
    problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    def __str__(self) -> str:
        return f"{self.user}'s submission to '{self.problem}'"


class Solution(
    AnswerModelBase,
    ScoreModelBase,
):
    """
    Solution model for user solution to be submit on problem,
    Submission : Solution (1:N)
    """

    class Meta:
        constraints = [
            ScoreModelBase.get_score_constraints("solution"),
        ]

    submission = models.ForeignKey(
        "Submission",
        on_delete=models.CASCADE,
        related_name="solutions",
    )

    def __str__(self) -> str:
        return (
            f"{self.submission.user} solution on {self.submission.problem}({self.pk})"
        )
