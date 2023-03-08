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


# TODO : duplicated
class ProblemCommentarySerializer(ModelSerializer):

    comment = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = ("comment",)

    def get_comment(self, obj):
        return CommentarySerializer(obj.commentary).data


class ProblemListSerializer(ModelSerializer):

    category = serializers.StringRelatedField(
        read_only=True
    )  # CategorySerializer(read_only=True)

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


class ProblemCreateUpdateSerializer(ModelSerializer):
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
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    commentary = CommentarySerializer()
    answer = AnswerSerializer()

    class Meta:
        model = Problem
        fields = "__all__"

    def validate_level(self, value):
        # TODO : delete when level field has check constraints
        if isinstance(value, int) and value in range(1, 6):
            return value
        raise ValidationError("level must be one of [1, 2, 3, 4, 5].")

    submodels = [
        ("answer", AnswerCreateSerializer),
        ("commentary", CommentaryCreateSerializer),
    ]

    def create(self, validated_data):

        # save submodels
        for key, serializer_class in self.submodels:
            serializer = serializer_class(data=validated_data.pop(key))
            serializer.is_valid(raise_exception=True)
            validated_data[key] = serializer.save()

        # add owner info
        validated_data["owner"] = self.context["request"].user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # save submodels
        for key, serializer_class in self.submodels:
            submodel_instance = getattr(instance, key)
            serializer = serializer_class(
                submodel_instance, data=validated_data.pop(key)
            )
            serializer.is_valid(raise_exception=True)
            validated_data[key] = serializer.save()

        return super().update(instance, validated_data)


class ProblemDetailSerializer(ModelSerializer):

    category = serializers.StringRelatedField(read_only=True)
    owner = serializers.StringRelatedField(read_only=True)

    # TODO : show link for commentary, answer?.

    class Meta:
        model = Problem
        exclude = (
            "commentary",
            "answer",
        )
