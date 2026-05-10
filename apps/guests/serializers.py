from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.ai_assistant.serializers import (
    AiDiagnosticSnapshotSerializer,
    AiMessageSerializer,
)
from apps.cases.serializers import CaseSerializer
from apps.identity.serializers import TokenPairSerializer, UserSerializer
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticChapter, DiagnosticChapterOption
from apps.troubleshooting.serializers import DiagnosticAdviceStepSerializer

User = get_user_model()


class GuestQuotaSerializer(serializers.Serializer):
    ai_turn_limit = serializers.IntegerField()
    ai_turns_used = serializers.IntegerField()
    ai_turns_remaining = serializers.IntegerField()
    message_limit = serializers.IntegerField()
    messages_used = serializers.IntegerField()
    messages_remaining = serializers.IntegerField()


class GuestSessionResponseSerializer(serializers.Serializer):
    guest_session_id = serializers.UUIDField()
    guest_token = serializers.CharField(required=False)
    status = serializers.CharField()
    expires_at = serializers.DateTimeField()
    quotas = GuestQuotaSerializer()


class GuestDiagnosticTurnSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)
    diagnostic_chapter_id = serializers.IntegerField(required=False, allow_null=True)
    diagnostic_chapter_option_id = serializers.IntegerField(required=False, allow_null=True)
    use_ai = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        chapter = None
        option = None
        chapter_id = attrs.get("diagnostic_chapter_id")
        option_id = attrs.get("diagnostic_chapter_option_id")

        if chapter_id is not None:
            try:
                chapter = DiagnosticChapter.objects.get(
                    id=chapter_id,
                    status=DiagnosticChapter.Statuses.PUBLISHED,
                    is_public=True,
                )
            except DiagnosticChapter.DoesNotExist as exc:
                raise serializers.ValidationError({"diagnostic_chapter_id": "Invalid diagnostic chapter."}) from exc

        if option_id is not None:
            try:
                option = DiagnosticChapterOption.objects.select_related("chapter").get(id=option_id, is_active=True)
            except DiagnosticChapterOption.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"diagnostic_chapter_option_id": "Invalid diagnostic chapter option."}
                ) from exc
            if option.chapter.status != DiagnosticChapter.Statuses.PUBLISHED or not option.chapter.is_public:
                raise serializers.ValidationError(
                    {"diagnostic_chapter_option_id": "Invalid diagnostic chapter option."}
                )
            if chapter is not None and option.chapter_id != chapter.id:
                raise serializers.ValidationError(
                    {"diagnostic_chapter_option_id": "Option does not belong to the selected chapter."}
                )
            chapter = chapter or option.chapter

        if attrs.get("use_ai", True) and not attrs.get("message", "").strip():
            raise serializers.ValidationError({"message": "Message is required when AI is requested."})

        self.context["diagnostic_chapter"] = chapter
        self.context["diagnostic_chapter_option"] = option
        return attrs


class GuestDiagnosticTurnResponseSerializer(serializers.Serializer):
    advice_steps = DiagnosticAdviceStepSerializer(many=True)
    user_message = AiMessageSerializer(allow_null=True)
    assistant_message = AiMessageSerializer(allow_null=True)
    diagnostic_snapshot = AiDiagnosticSnapshotSerializer(allow_null=True)
    quotas = GuestQuotaSerializer()
    call_to_action = serializers.DictField(allow_empty=True)


class GuestPromotionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    case_title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    case_description = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        normalized_value = User.objects.normalize_email(value)
        if User.objects.filter(email=normalized_value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_category_id(self, value):
        if value is None:
            return value
        try:
            category = Category.objects.get(id=value, is_active=True)
        except Category.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid category.") from exc
        self.context["category"] = category
        return value

    def validate(self, attrs):
        if "category" in self.context:
            attrs["category"] = self.context["category"]
        return attrs


class GuestPromotionResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = TokenPairSerializer()
    guest_session = GuestSessionResponseSerializer()
    case = CaseSerializer()
    diagnostic_snapshot = AiDiagnosticSnapshotSerializer(allow_null=True)
