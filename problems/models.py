from django.db import models
from django.contrib.auth.models import User

from config import redis  # custom redis interface

from .models_abstract import (
    DelayManager,
    AutoTimeTrackingModelBase,
    AnswerModelBase,
    ScoreModelBase,
    _T,
    _QS,
)


SEPARATOR = ","

# use .format()
PROBLEM_KEY = "problems.{}"


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

            hit = self.filter(query)
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

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ) -> None:
        super().save(force_insert, force_update, using, update_fields)

        pk = self.pk
        key = PROBLEM_KEY.format(pk)

        hit = redis.get(key)
        if hit:
            # update cache
            redis.set(key, self)


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
        try:
            submission = Submission.objects.find_submission_on_problem(problem_id, user)
        except Submission.DoesNotExist:
            raise Solution.DoesNotExist

        return self.filter(submission=submission).order_by("-created_at")


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
