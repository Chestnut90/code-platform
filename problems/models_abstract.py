from django.db import models


class AutoTimeTrackingModelBase(models.Model):
    """Abstract class for creation time and updated time"""

    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
