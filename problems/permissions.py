from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS,
)


class IsOwnerOrReadOnly(BasePermission):
    """Check permission of model which hold 'owner' field"""

    def has_object_permission(self, request, view, obj):
        """
        Check request auth with object owner attribute,
        when method is not UN_SAFE_METHOD(?)
        """
        assert hasattr(obj, "owner"), "object does not have 'owner' attribute"

        return bool(
            request.method in SAFE_METHODS or request.user and request.user == obj.owner
        )


class IsOwnerOrSolvedUserReadOnly(BasePermission):
    """
    Permission to user who solved problem.
    """

    def has_object_permission(self, request, view, obj):

        if request.user == obj.owner:
            return True

        submissions = request.user.submissions
        return submissions and submissions.filter(problem=obj, score=100).exists()
