from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    SAFE_METHODS,
)
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)
from rest_framework.status import HTTP_204_NO_CONTENT

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    CategorySerializer,
    ProblemListSerializer,
    ProblemCreateUpdateSerializer,
    ProblemDetailSerializer,
    AnswerSerializer,
    ProblemCommentarySerializer,
    SubmissionSerializer,
    SolutionReadCreateSerializer,
)
from .models import Problem, Category, Submission, Solution
from .permissions import IsOwnerOrReadOnly, IsOwnerOrSolvedUserReadOnly
from .filters import (
    NotSolvedProblemsFilter,
    MinLevelProblemFilter,
    LessSubmittedProblemFilter,
    LastestProblemFilter,
)  ### recommendation api


class CategoriesAPI(ListAPIView):
    """
    Categories API for list-up categories
    """

    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CategorySerializer


class ProblemsAPI(ListCreateAPIView):
    """
    Problems api
    """

    queryset = Problem.objects.all()
    serializer_class = ProblemListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    # filter_backends = [NotSolvedProblemsFilter]
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

    @swagger_auto_schema(
        operation_description="GET problems with query parameters",
        manual_parameters=[
            openapi.Parameter(
                name="levels",
                in_=openapi.IN_QUERY,
                description="Problems levels want to get, ex) 'levels=1,2' for level 1 and 2",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                name="categories",
                in_=openapi.IN_QUERY,
                description="Problems categories want to get, ex) 'categories=1,2' for category 1 and 2",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={"404": "Not Found"},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Add problem",
        request_body=ProblemCreateUpdateSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


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


class ProblemSubmissionAPI(RetrieveAPIView):
    """
    Submission api with problem_id
    """

    queryset = None  # use get_queryset instead
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        id = self.kwargs["pk"]
        user = self.request.user
        try:
            return Submission.objects.find_submission_on_problem(
                problem_id=id, user=user
            )
        except Submission.DoesNotExist:
            raise NotFound

    def get(self, request, *args, **kwargs):
        obj = self.get_queryset()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


class ProblemSolutionAPI(ListCreateAPIView):
    """
    solution submit api
    """

    queryset = None  # use get_queryset instead
    serializer_class = SolutionReadCreateSerializer
    permission_classes = [IsAuthenticated]  # TODO : block to owner?
    pagination_class = None  # TODO : pagination?

    def get_queryset(self):
        pk = self.kwargs["pk"]
        try:
            return Solution.objects.find_submitted_solutions(pk, self.request.user)
        except Solution.DoesNotExist:
            raise NotFound


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
