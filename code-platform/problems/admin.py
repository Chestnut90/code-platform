from django.contrib import admin

from .models import (
    Problem,
    Category,
    Answer,
    Commentary,
    Submission,
    Solution,
)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass


@admin.register(Commentary)
class CommentaryModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    pass
