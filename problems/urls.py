from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProblemsAPI.as_view()),
    path("<int:pk>", views.ProblemAPI.as_view()),
]
