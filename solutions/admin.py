from django.contrib import admin

from .models import Submission, Solution


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    pass
