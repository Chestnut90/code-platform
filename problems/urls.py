from django.urls import path

from . import views

urlpatterns = [
    path("", views.ProblemsAPI.as_view()),
    path("categories", views.CategoriesAPI.as_view()),
    path("<int:pk>", views.ProblemAPI.as_view()),
    path("<int:pk>/answer", views.ProblemAnswerAPI.as_view()),
    path("<int:pk>/commentary", views.ProblemCommentaryAPI.as_view()),
    path("<int:pk>/submission", views.ProblemSubmissionAPI.as_view()),
    path("<int:pk>/solutions", views.ProblemSolutionAPI.as_view()),
    path("recommendation", views.RecommendProblemAPI.as_view()),
]
