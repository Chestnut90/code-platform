from django.contrib.auth.models import User

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

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
            "id",
            "name",
            "level",
            "category",
        )


class ProblemCreateSerializer(ModelSerializer):
    """
    Problem create serializer
    """

    class AnswerCreateSerializer(ModelSerializer):
        """Problem-Answer create serializer"""

        class Meta:
            model = Answer
            fields = ("answer",)

    class CommentaryCreateSerializer(ModelSerializer):
        """Problem Commentary create serializer"""

        class Meta:
            model = Commentary
            fields = ("comment",)

    owner = UserSerializer(read_only=True)  # TODO : using request.user auth.
    # TODO : customize, category pk error message
    # TODO : show category string when get method.
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    commentary = CommentarySerializer()
    answer = AnswerSerializer()

    class Meta:
        model = Problem
        fields = "__all__"

    def is_valid(self, *, raise_exception=False):
        return super().is_valid(raise_exception=raise_exception)

    def validate_level(self, value):
        # TODO : delete when level field has check constraints
        if isinstance(value, int) and value in range(1, 6):
            return value
        raise ValidationError("level must be one of [1, 2, 3, 4, 5].")

    def create(self, validated_data):
        # add answer, commnetary fk
        keys = ["answer", "commentary"]
        serializer_classes = [
            self.AnswerCreateSerializer,
            self.CommentaryCreateSerializer,
        ]
        for key, serializer_class in zip(keys, serializer_classes):
            serializer = serializer_class(data=validated_data.pop(key))
            serializer.is_valid(raise_exception=True)
            validated_data[key] = serializer.save()

        # add owner info
        validated_data["owner"] = self.context["request"].user

        return super().create(validated_data)
