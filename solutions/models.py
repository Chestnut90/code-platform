from django.db import models
from django.contrib.auth.models import User


from problems.models_abstract import AutoTimeTrackingModelBase


class Submission(AutoTimeTrackingModelBase):
    """
    Submission Model definition,
    (user, problem) : submission => (1 : 1)
    """

    # TODO : unique(user, problem)

    # user who submit
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.CASCADE,
        related_name="submissions",
    )

    score = models.PositiveSmallIntegerField()  # 0 or 100

    def __str__(self) -> str:
        return f"{self.user} submit {self.problem}"


class Solution(AutoTimeTrackingModelBase):
    """
    Solution model for user solution to be submit on problem,
    Submission : Solution (1:N)
    """

    score = models.PositiveSmallIntegerField()  # 0 or 100
    solution = models.TextField()

    submission = models.ForeignKey(
        "Submission",
        on_delete=models.CASCADE,
        related_name="solutions",
    )

    def __str__(self) -> str:
        return (
            f"{self.submission.user} solution on {self.submission.problem}({self.pk})"
        )
