from django.db import models
from django.contrib.auth.models import User


from .models_abstract import (
    AutoTimeTrackingModelBase,
    AnswerModelBase,
    ScoreModelBase,
)

from .managers import (
    ProblemManager,
    SolutionManager,
    SubmissionManager,
    update_problem_cache,
)


class Answer(AnswerModelBase):
    """Problem answer model, submit by problem owner"""

    def __str__(self) -> str:
        return f"answer of {self.problem}" if hasattr(self, "problem") else "deleted"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert, force_update, using, update_fields)
        update_problem_cache(self)


class Commentary(AutoTimeTrackingModelBase):
    """Problem Commentary model, submit by problem owner"""

    comment = models.TextField()

    def __str__(self) -> str:
        return f"comment of {self.problem}" if hasattr(self, "problem") else "deleted"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert, force_update, using, update_fields)
        update_problem_cache(self)


class Category(AutoTimeTrackingModelBase):
    """Category of Problem model definition"""

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    def __str__(self) -> str:
        return f"{self.name}"


class Problem(AutoTimeTrackingModelBase):
    """Problem model definition"""

    objects = ProblemManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(level__gte=1, level__lte=5), name="level_range"
            ),
        ]

    # name of this problem.
    name = models.CharField(max_length=50, unique=True)
    # problem level (1 to 5)
    level = models.PositiveSmallIntegerField()
    # string about problem
    description = models.TextField()
    # TODO : how to set default key
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
        return self.submissions.count()

    def solved_count(self):
        return len([1 for i in list(self.submissions.all()) if i.score == 100])

    def __str__(self) -> str:
        return f"{self.name}"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ) -> None:
        super().save(force_insert, force_update, using, update_fields)
        update_problem_cache(self)


class Submission(
    AutoTimeTrackingModelBase,
    ScoreModelBase,
):
    """
    Submission Model definition,
    (user, problem) : submission => (1 : 1)
    """

    objects = SubmissionManager()

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
        return f"{self.user_id} to {self.problem_id} submission {self.score}"


class Solution(
    AnswerModelBase,
    ScoreModelBase,
):
    """
    Solution model for user solution to be submit on problem,
    Submission : Solution (1:N)
    """

    CHECK_BEFORE = "check_before"
    CHEKING = "checking"
    CHECK_DONE = "check_done"

    class CheckStateChoice(models.TextChoices):
        CHECK_BEFORE = ("check_before", "Check Before")
        CHECKING = ("checking", "Checking")
        CHECK_DONE = ("check_done", "Check Done")

    objects = SolutionManager()

    class Meta:
        constraints = [
            ScoreModelBase.get_score_constraints("solution"),
        ]

    submission = models.ForeignKey(
        "Submission",
        on_delete=models.CASCADE,
        related_name="solutions",
    )

    state = models.CharField(
        max_length=12,
        choices=CheckStateChoice.choices,
        default=CHECK_BEFORE,
    )

    def __str__(self) -> str:
        return (
            f"{self.submission.user} solution on {self.submission.problem}({self.pk})"
        )
