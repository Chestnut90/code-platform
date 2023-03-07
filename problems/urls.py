from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProblemsAPI.as_view()),
]
