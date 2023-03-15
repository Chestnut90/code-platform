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

    name = models.CharField(
        max_length=50,
        unique=True,
    )

    def __str__(self) -> str:
        return f"{self.name}"


class ProblemManager(models.Manager):
    """
    Problem model manager
    do queries.
    """

    SEPARATOR = ","

    def _list_queries(self, field_name, values: list) -> models.Q:
        query = models.Q()
        for value in values:
            query |= models.Q(**{field_name: value})
        return query

    def get_queriedset(self, levels=None, categories=None):

        queryset = self.all()
        query = models.Q()
        if levels:
            query &= self._list_queries("level", levels.split(self.SEPARATOR))
        if categories:
            query &= self._list_queries("category", categories.split(self.SEPARATOR))
        # TODO : query with rate of solved

        return queryset.filter(query)

    def check_answer(self, problem_id, answer):
        """
        check problem answer with given answer.\n
        can raise Problem.DoesNotExist
        """
        problem = self.get(pk=problem_id)

        return 100 if problem.answer.answer == answer else 0


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
        return self.submissions.all().count()

    def solved_count(self):
        return self.submissions.filter(score=100).count()

    def __str__(self) -> str:
        return f"{self.name}"


class SubmissionManager(models.Manager):
    def find_submission_on_problem(self, problem_id, user):
        """
        find submission instance with problem_id and user object
        can raise Submission.DoesNotFound
        """
        return self.get(models.Q(problem=problem_id) & models.Q(user=user.id))


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
        return f"{self.user}'s submission to '{self.problem}'"


class SolutionManager(models.Manager):
    def find_submitted_solutions(self, problem_id, user):
        """
        find solutions of problem which user submitted.
        ordered by lastest submitted solutions.
        """
        queryset = self.all()
        try:
            submission = Submission.objects.find_submission_on_problem(problem_id, user)
        except Submission.DoesNotExist:
            raise Solution.DoesNotExist

        return queryset.filter(submission=submission).order_by("-created_at")


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
