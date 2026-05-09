from rest_framework import serializers

from apps.ai_assistant.serializers import (
    AiDiagnosticSnapshotSerializer,
    AiMessageSerializer,
)
from apps.troubleshooting.models import DiagnosticChapter, DiagnosticChapterOption
from apps.troubleshooting.serializers import DiagnosticAdviceStepSerializer


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
