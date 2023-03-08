from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    BasePermission,
    SAFE_METHODS,
)
from rest_framework.pagination import PageNumberPagination

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)


from .serializers import (
    ProblemListSerializer,
    ProblemCreateSerializer,
    ProblemDetailSerializer,
)
from .models import Problem


class ProblemsAPI(ListCreateAPIView):
    """
    Problems GET(list)
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
        return ProblemCreateSerializer


class ProblemAPI(RetrieveUpdateDestroyAPIView):
    """
    Problem API
    """

    class IsOwner(BasePermission):
        """Check permission of model which hold 'owner' field"""

        def has_object_permission(self, request, view, obj):
            """
            Check request auth with object owner attribute,
            when method is not UN_SAFE_METHOD(?)
            """
            assert hasattr(obj, "owner"), "object does not have 'owner' attribute"

            return bool(request.method in SAFE_METHODS or request.user is obj.owner)

    queryset = Problem.objects.all()
    serializer_class = ProblemDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]
