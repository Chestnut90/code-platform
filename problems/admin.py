from django.contrib import admin

from .models import (
    Problem,
    Category,
    Answer,
    Commentary,
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
