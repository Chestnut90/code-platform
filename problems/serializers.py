from django.contrib.auth.models import User

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .models import Problem, Category, Answer, Commentary, Submission, Solution


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
        fields = (
            "id",
            "name",
        )
        read_only_fields = ("id",)


class AnswerSerializer(ModelSerializer):
    """Problem-Answer serializer"""

    class Meta:
        model = Answer
        fields = "__all__"


class CommentarySerializer(ModelSerializer):
    """Problem-commentary serializer"""

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


class ProblemSerializerBase(ModelSerializer):
    """Abstract serializer for problem read."""

    owner = serializers.StringRelatedField(read_only=True)
    category = serializers.StringRelatedField(read_only=True)

    submitted_count = serializers.SerializerMethodField()
    solved_count = serializers.SerializerMethodField()

    class Meta:
        model = Problem

    def get_submitted_count(self, obj):
        return obj.submitted_count()

    def get_solved_count(self, obj):
        return obj.solved_count()


class ProblemListSerializer(ProblemSerializerBase):
    """Problem list serializer for Problems api GET"""

    class Meta:
        model = Problem
        fields = (
            "id",
            "name",
            "level",
            "category",
            "owner",
            "submitted_count",
            "solved_count",
            # TODO : user solved
        )


class ProblemCreateUpdateSerializer(ModelSerializer):
    """
    Problem Create, Update serializer for Problems and Problem POST, PUT, PATCH
    """

    owner = serializers.StringRelatedField(read_only=True)
    # TODO : customize, category pk error message
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    commentary = CommentarySerializer()
    answer = AnswerSerializer()

    class Meta:
        model = Problem
        fields = "__all__"

    def validate_level(self, value):
        _range = range(1, 6)
        if isinstance(value, int) and value in _range:
            return value
        raise ValidationError(f"level must be one of {list(_range)}.")

    nested_models = [
        ("answer", AnswerSerializer),
        ("commentary", CommentarySerializer),
    ]

    def save_nested(self, validated_data, partial=False):
        """
        save nested model with defined in self.nested_models
        """
        for key, serializer_class in self.nested_models:
            instance = getattr(self.instance, key, None) if partial else None
            data = validated_data.pop(key, None)
            if not data:
                continue
            serializer = serializer_class(instance=instance, data=data, partial=partial)
            serializer.is_valid(raise_exception=True)
            validated_data[key] = serializer.save()

    def create(self, validated_data):
        self.save_nested(validated_data)

        # add owner info
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self.save_nested(validated_data, partial=True)
        return super().update(instance, validated_data)


class ProblemDetailSerializer(ProblemSerializerBase):

    # TODO : show link for commentary, answer?.

    class Meta:
        model = Problem
        exclude = (
            "commentary",
            "answer",
        )


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = "__all__"


class SolutionReadCreateSerializer(serializers.ModelSerializer):

    submission = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Solution
        fields = "__all__"
        read_only_fields = (
            "submission",
            "score",
        )

    def _get_submission(self, problem_id, user):
        """
        get submission for problem and user.
        if not existed then create new submission instance
        """

        try:
            submission = Submission.objects.find_submission_on_problem(problem_id, user)
        except Submission.DoesNotExist:
            serializer = SubmissionSerializer(
                data={"user": user.pk, "problem": problem_id}
            )
            serializer.is_valid(
                raise_exception=True
            )  # raise 400 BAD_REQUEST, problem not exist
            submission = serializer.save()

        return submission

    def create(self, validated_data):
        # TODO : atomic transaction?

        problem_id = self.context["view"].kwargs["pk"]
        user = self.context["request"].user  # TODO : check Anonymous?

        submission = self._get_submission(problem_id, user)
        score = Problem.objects.check_answer(problem_id, validated_data["answer"])

        # add submission and score into validated_data
        validated_data["submission"] = submission
        validated_data["score"] = score

        # create instance
        instance = super().create(validated_data)

        # update submission score
        if validated_data["score"] == 100:
            serializer = SubmissionSerializer(
                submission, data={"score": validated_data["score"]}, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return instance
