from django.contrib.auth.models import User

from rest_framework.serializers import ModelSerializer

from .models import Problem, Category, Answer, Commentary


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "last_name",
            "first_name",
        )


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ("category",)


class AnswerSerializer(ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class CommentarySerializer(ModelSerializer):
    class Meta:
        model = Commentary
        fields = "__all__"


class ProblemListSerializer(ModelSerializer):

    category = CategorySerializer(read_only=True)

    # TODO : sumitted field
    # TODO : correct solutions field

    class Meta:
        model = Problem
        fields = (
            "name",
            "level",
            "category",
        )
