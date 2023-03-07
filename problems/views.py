from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination

from rest_framework.generics import ListCreateAPIView

from .serializers import ProblemListSerializer
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
