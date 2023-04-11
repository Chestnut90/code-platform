from django.db import models


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
