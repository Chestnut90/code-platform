from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    SAFE_METHODS,
)
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_202_ACCEPTED
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    CategorySerializer,
    ProblemListSerializer,
    ProblemCreateUpdateSerializer,
    SubmissionSerializer,
    SolutionSerializer,
)
from .models import Problem, Category, Submission, Solution
from .permissions import IsOwnerOrReadOnly, IsOwnerOrSolvedUserReadOnly
from .filters import (
    NotSolvedProblemsFilter,
    MinLevelProblemFilter,
    LessSubmittedProblemFilter,
    LastestProblemFilter,
)  ### recommendation api

from .tasks import check_answer_and_update_score


id_parameter = openapi.Parameter(
    "id",
    openapi.IN_PATH,
    description="id of problem",
    type=openapi.TYPE_INTEGER,
)
level_parameter = openapi.Parameter(
    name="levels",
    in_=openapi.IN_QUERY,
    description="Level query parameters with integer and comma separated. ex) 'levels=1,2' for level 1 and 2",
    type=openapi.TYPE_STRING,
)
category_parameter = openapi.Parameter(
    name="categories",
    in_=openapi.IN_QUERY,
    description="Category query parameters with integer and comma separated. ex) 'categories=1,2' for category 1 and 2",
    type=openapi.TYPE_STRING,
)
not_found_response = openapi.Response("not found")
bad_request_response = openapi.Response("bad request")

SolutionPostSuccessSchema = openapi.Schema(
    type=openapi.TYPE_OBJECT, properties={"task": ""}
)


class ProblemViewSet(ModelViewSet):
    """Problem View, all view"""

    # queryset = Problem.objects
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    serializer_class = ProblemListSerializer
    # TODO : receive page and page_size, customize
    pagination_class = PageNumberPagination

    problem_url = ["problems-detail", "problems-list"]  # names of problems

    def get_serializer_class(self):
        """
        Choose suitable serializer for request method.
        override from GenericAPIView.
        """

        current_url = self.request.resolver_match.url_name

        if current_url in self.problem_url:
            if self.request.method in SAFE_METHODS:
                return ProblemListSerializer
            return ProblemCreateUpdateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """
        queryset from filtered by url parameters, levels and categories
        """
        levels = self.request.query_params.get("levels", "")
        categories = self.request.query_params.get("categories", "")
        return Problem.objects.get_cached_queryset(levels=levels, categories=categories)

    def get_object(self):
        id = self.kwargs["pk"]
        try:
            obj = Problem.objects.get_cached_problem(id)
        except Problem.DoesNotExist:
            raise NotFound

        self.check_object_permissions(self.request, obj)
        return obj

    def perform_destroy(self, instance):
        submodels = [instance.answer, instance.commentary]
        super().perform_destroy(instance)
        for submodel in submodels:
            submodel.delete()

    @swagger_auto_schema(
        operation_description="GET problems with query parameters",
        manual_parameters=[level_parameter, category_parameter],
        paginator=PageNumberPagination,
        responses={
            # TODO : paginated response..
            "200": openapi.Response(
                "success response, paginated", schema=ProblemListSerializer(many=True)
            ),
            "404": not_found_response,
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="GET problem with given id",
        manual_parameters=[id_parameter],
        responses={"404": not_found_response},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Add problem api. Only authenticated user can add problem. ",
        request_body=ProblemCreateUpdateSerializer,
        responses={
            "400": openapi.Response(
                "bad request", schema=ProblemCreateUpdateSerializer(data=None)
            )
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        API to update problem with partial data.\n
        Use this api when update problem, answer, comment.
        """,
        manual_parameters=[id_parameter],
        request_body=ProblemCreateUpdateSerializer,
        responses={
            "200": openapi.Response(
                "success response", schema=ProblemCreateUpdateSerializer()
            )
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        API to update problem with whole data.\n
        User this api when update problem, answer, comment.
        """,
        manual_parameters=[id_parameter],
        request_body=ProblemCreateUpdateSerializer,
        responses={
            "404": not_found_response,
            "400": bad_request_response,
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""API to delete problem match with id.""",
        manual_parameters=[id_parameter],
        responses={
            "204": openapi.Response("success response"),
            "404": not_found_response,
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="""
        API to check answer and commentary of problem with id.
        Authenticated and Solved user can get response.
        """,
        manual_parameters=[id_parameter],
        responses={
            "403": openapi.Response("failed response, request user not solve problem."),
            "404": not_found_response,
        },
    )
    @action(
        methods=["get"],
        detail=True,
        url_path="answer-commentary",
        url_name="answer_commentary",
        permission_classes=[
            IsAuthenticated,
            IsOwnerOrSolvedUserReadOnly,
        ],
        serializer_class=ProblemCreateUpdateSerializer,
    )
    def answer_commentary(self, request, pk=None):
        try:
            obj = Problem.objects.get_cached_problem(pk)
        except Problem.DoesNotExist:
            raise NotFound

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get all categories data.",
        paginator=None,
        responses={
            "200": openapi.Response("success response", CategorySerializer(many=True)),
        },
    )
    @action(
        methods=["get"],
        detail=False,
        pagination_class=None,
    )
    def categories(self, request):
        """categories of problem"""
        serializer = CategorySerializer(Category.objects.all(), many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="""
        Recommend single problem.\n
        given problem is follow order in below.\n
        1. lowest level.\n
        2. less subbmited.\n
        3. latest added problem.\n
        and not solved problem.""",
        responses={
            "200": openapi.Response(
                "success description", schema=ProblemListSerializer()
            ),
            "204": openapi.Response("success but, no problem to recommend"),
        },
    )
    @action(
        methods=["get"],
        detail=False,
        url_path="recommendation",
        url_name="recommendation",
        filter_backends=[
            NotSolvedProblemsFilter,
            MinLevelProblemFilter,
            LessSubmittedProblemFilter,
            LastestProblemFilter,
        ],
        pagination_class=None,
    )
    def recommendation(self, request):
        """recommendate problem to user"""
        queryset = self.filter_queryset(self.get_queryset())
        if queryset.exists():
            serializer = self.get_serializer(queryset.first())
            return Response(serializer.data)

        return Response(status=HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_description="Brief information of submitted solution to problem by user",
        manual_parameters=[id_parameter],
        responses={
            "204": openapi.Response("success, but user not submit any solution.")
        },
    )
    @action(
        methods=["get"],
        detail=True,
        url_path="submission",
        url_name="submission",
        permission_classes=[IsAuthenticated],
        serializer_class=SubmissionSerializer,
    )
    def submission(self, request, pk):
        try:
            obj = Submission.objects.find_submission_on_problem(
                problem_id=pk, user=request.user
            )
        except Submission.DoesNotExist:
            return Response(status=HTTP_204_NO_CONTENT)

        return Response(self.get_serializer(obj).data)

    @swagger_auto_schema(
        method="get",
        operation_description="""API to list-up solutions which user submit to problem.""",
        manual_parameters=[id_parameter],
        responses={
            "200": openapi.Response(
                "success response", schema=SolutionSerializer(many=True)
            ),
            "204": openapi.Response("success, but use not submit any solution."),
        },
    )
    @swagger_auto_schema(
        method="post",
        operation_description="""API to submit solutions.""",
        manual_parameters=[id_parameter],
        request_body=SolutionSerializer,
        responses={
            "202": openapi.Response(
                "success response",  # TODO : dict to schema
            ),
            "400": bad_request_response,
            "404": openapi.Response("failed, no problem matched."),
        },
    )
    @action(
        methods=["get", "post"],
        detail=True,
        url_path=r"solutions",
        url_name="solutions",
        serializer_class=SolutionSerializer,
    )
    def solutions_list_post(self, request, pk):
        def _list(self, request, pk):
            try:
                obj = Solution.objects.find_submitted_solutions(pk, self.request.user)
            except Solution.DoesNotExist:
                return Response(status=HTTP_204_NO_CONTENT)

            return Response(
                self.get_serializer(obj, many=True).data,
            )

        def _post(self, request, pk):

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            solution_id = serializer.data["id"]

            ret = check_answer_and_update_score.delay(pk, solution_id)

            return Response(
                {
                    "task": {
                        "href": f"problems/{pk}/solutions/{solution_id}",
                    }
                },
                status=HTTP_202_ACCEPTED,
            )

        method = _list if request.method in SAFE_METHODS else _post
        return method(self, request, pk)

    @swagger_auto_schema(
        operation_description="""""",
        manual_parameters=[
            id_parameter,
            openapi.Parameter(
                "solution_id",
                openapi.IN_PATH,
                description="id of solution",
                type=openapi.TYPE_INTEGER,
            ),
        ],
        responses={
            "200": openapi.Response("success response", schema=SolutionSerializer()),
            "404": not_found_response,
        },
    )
    @action(
        methods=["get"],
        detail=True,
        url_path=r"solutions/(?P<solution_id>[^/.]+)",
        url_name="solutions-detail",
        serializer_class=SolutionSerializer,
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def solutions_id(self, request, pk, solution_id):
        try:
            obj = Solution.objects.find_submitted_solutions(pk, self.request.user)
        except Solution.DoesNotExist:
            return Response(status=HTTP_204_NO_CONTENT)

        obj = obj.get(pk=solution_id)
        return Response(self.serializer_class(obj).data)
