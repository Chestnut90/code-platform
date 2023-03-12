from django.db.models import QuerySet, Min, Count

from rest_framework.filters import BaseFilterBackend


class NotMineProblemsFilter(BaseFilterBackend):
    """
    For problem model filter to exclude mines
    """

    def filter_queryset(self, request, queryset, view):
        return queryset.exclude(onwer=request.user)


class NotSolvedProblemsFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        query = {
            "submissions__user": request.user,
            "submissions__score": 100,
        }
        return queryset.exclude(**query)


class MinLevelProblemFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset: QuerySet, view):
        # TODO : error handling
        min = queryset.aggregate(Min("level"))["level__min"]
        return queryset.filter(level=min)


class LessSubmittedProblemFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset: QuerySet, view):
        queryset = queryset.annotate(submissions_count=Count("submissions"))
        min = queryset.aggregate(Min("submissions_count"))["submissions_count__min"]
        return queryset.filter(submissions_count=min)


class LastestProblemFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset: QuerySet, view):
        return queryset.order_by("-created_at")  # TODO : single or queryset?
