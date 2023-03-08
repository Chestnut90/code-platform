from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    SAFE_METHODS,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)

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


class ProblemsAPI(ListCreateAPIView):
    """
    Problems list and create api,
    support get and post
    """

    queryset = Problem.objects.all()
    serializer_class = ProblemListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
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
