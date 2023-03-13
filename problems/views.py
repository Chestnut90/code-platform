from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    SAFE_METHODS,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)
from rest_framework.status import HTTP_204_NO_CONTENT

from .serializers import (
    ProblemListSerializer,
    ProblemCreateUpdateSerializer,
    ProblemDetailSerializer,
    AnswerSerializer,
    CommentarySerializer,
    ProblemCommentarySerializer,
)
from .models import Problem
from .permissions import IsOwnerOrReadOnly, IsOwnerOrSolvedUserReadOnly


### recommendation api

from .filters import (
    NotSolvedProblemsFilter,
    MinLevelProblemFilter,
    LessSubmittedProblemFilter,
    LastestProblemFilter,
)


class ProblemsAPI(ListCreateAPIView):
    """
    Problems api,
    GET, with parameters
        example, 'problems?categories=1,2&levels=1,2'
    support get and post
    """

    queryset = Problem.objects.all()
    serializer_class = ProblemListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [NotSolvedProblemsFilter]
    pagination_class = (
        PageNumberPagination  # TODO : receive page and page_size, customize
    )

    def get_serializer_class(self):
        """
        Choose suitable serializer for request method.
        override from GenericAPIView.
        """

        if self.request.method in SAFE_METHODS:
            return ProblemListSerializer
        return ProblemCreateUpdateSerializer

    def get_queryset(self):
        """
        queryset from filtered by url parameters, levels and categories
        """
        levels = self.request.query_params.get("levels", None)
        categories = self.request.query_params.get("categories", None)
        return Problem.objects.get_queriedset(levels=levels, categories=categories)


class ProblemAPI(RetrieveUpdateDestroyAPIView):
    """
    Problem API
    """

    queryset = Problem.objects.all()
    serializer_class = None  # use get_serializer_class instead
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ProblemDetailSerializer
        return ProblemCreateUpdateSerializer

    def perform_destroy(self, instance):
        submodels = [instance.answer, instance.commentary]
        super().perform_destroy(instance)
        for submodel in submodels:
            submodel.delete()


class ProblemAnswerAPI(RetrieveAPIView):
    """Problem Answer retrieve api for only user who solved problem."""

    queryset = Problem.objects.all()
    serializer_class = AnswerSerializer  # TODO : check, how to works?
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrSolvedUserReadOnly,
    ]  # TODO : IsOwnerOrSolvedUserReadOnly error message


class ProblemCommentaryAPI(RetrieveAPIView):
    """Problem Commentary retrieve api for only user who solved problem."""

    queryset = Problem.objects.all()
    serializer_class = ProblemCommentarySerializer
    permission_classes = [
        IsAuthenticated,
        IsOwnerOrSolvedUserReadOnly,
    ]


from .models import Solution, Submission
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter, BaseFilterBackend


class ProblemSubmissionAPI(RetrieveAPIView):
    class SubmissionRetrieveSerializer(serializers.ModelSerializer):
        class Meta:
            model = Submission
            fields = "__all__"

    queryset = Submission.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionRetrieveSerializer

    def filter_queryset(self, queryset):
        try:
            try:
                problem = Problem.objects.get(pk=self.kwargs["pk"])
            except Problem.DoesNotExist:
                raise NotFound
            return queryset.get(user=self.request.user, problem=problem)
        except Submission.DoesNotExist:
            raise NotFound

    def get(self, request, *args, **kwargs):
        obj = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class ProblemSolutionAPI(ListCreateAPIView):
    """
    solution submit api
    """

    # class User
    # get, url = "problems/<int:pk>/solutions"
    # post, url = 'problems/<int:pk>/solutions

    class SolutionSerializer(serializers.ModelSerializer):
        class Meta:
            model = Solution
            fields = "__all__"

    class SolutionCreateSerializer(serializers.ModelSerializer):

        submission = serializers.PrimaryKeyRelatedField(read_only=True)

        class Meta:
            model = Solution
            fields = "__all__"
            read_only_fields = ("score",)

        def create(self, validated_data):
            # TODO : refactoring to before and after creation.
            # TODO : atomic transaction

            # check submission existed
            problem_id = self.context["view"].kwargs["pk"]
            user = self.context["request"].user
            problem = Problem.objects.get(pk=problem_id)

            query_kwargs = {"user": user, "problem": problem}

            from django.db.models import Q

            class SubmissionCreateSerializer(serializers.ModelSerializer):
                class Meta:
                    model = Submission
                    fields = "__all__"

            if not Submission.objects.filter(Q(user=user, problem=problem)).exists():
                serializer = SubmissionCreateSerializer(
                    data={"user": user.pk, "problem": problem.pk}  # TODO : simplify
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            submission = Submission.objects.get(Q(user=user, problem=problem))
            validated_data["submission"] = submission

            # TODO : move to bussiness logic
            # check submitted answer with problem answer
            validated_data["score"] = (
                100 if problem.answer.answer == validated_data["answer"] else 0
            )

            # update submission score
            if validated_data["score"] == 100:
                serializer = SubmissionCreateSerializer(
                    submission, data={"score": validated_data["score"]}, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            return super().create(validated_data)

    queryset = Solution.objects.all()
    serializer_class = None  # use get_serializer_class instead.
    permission_classes = [IsAuthenticated]  # TODO : block to owner?
    filter_backends = []  # TODO : order solution by desc
    pagination_class = None  # TODO : pagination

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return self.SolutionSerializer
        return self.SolutionCreateSerializer


class RecommendProblemAPI(RetrieveAPIView):
    """
    Recommend Problem api for user,
    """

    queryset = Problem.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ProblemDetailSerializer
    filter_backends = [
        NotSolvedProblemsFilter,
        MinLevelProblemFilter,
        LessSubmittedProblemFilter,
        LastestProblemFilter,
    ]

    def get(self, request):

        queryset = self.filter_queryset(self.get_queryset())

        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)

        return Response(
            {"result": "no problems to recommend."},
            status=HTTP_204_NO_CONTENT,
        )
