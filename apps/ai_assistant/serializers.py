from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.cases.models import Case
from apps.identity.models import User
from apps.troubleshooting.models import DiagnosticChapter, DiagnosticChapterOption

from .context import estimate_token_count
from .models import AiContextDigest, AiDiagnosticSnapshot, AiMessage, AiSession
from .usage import AiUsageLimitExceeded, enforce_ai_usage_limits


TERMINAL_CASE_STATUSES = {
    Case.Statuses.RESOLVED,
    Case.Statuses.CLOSED,
    Case.Statuses.CANCELLED,
}


class AiMessageSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source="session.id", read_only=True)

    class Meta:
        model = AiMessage
        fields = ("id", "session_id", "role", "content", "status", "error_detail", "metadata_json", "created_at")
        read_only_fields = fields


class AiDiagnosticSnapshotSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source="session.id", read_only=True)
    source_message_id = serializers.IntegerField(source="source_message.id", read_only=True, allow_null=True)
    diagnostic_chapter_id = serializers.IntegerField(source="diagnostic_chapter.id", read_only=True, allow_null=True)
    diagnostic_chapter_option_id = serializers.IntegerField(
        source="diagnostic_chapter_option.id",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AiDiagnosticSnapshot
        fields = (
            "id",
            "session_id",
            "source_message_id",
            "diagnostic_chapter_id",
            "diagnostic_chapter_option_id",
            "summary",
            "risk_level",
            "next_question",
            "escalation_recommended",
            "escalation_reason",
            "recommendation",
            "facts_json",
            "excluded_facts_json",
            "asked_questions_json",
            "safety_notes_json",
            "compacted_summary",
            "context_version",
            "context_metadata_json",
            "raw_payload_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AiContextDigestSerializer(serializers.ModelSerializer):
    session_id = serializers.IntegerField(source="session.id", read_only=True)
    from_message_id = serializers.IntegerField(source="from_message.id", read_only=True, allow_null=True)
    to_message_id = serializers.IntegerField(source="to_message.id", read_only=True, allow_null=True)
    source_snapshot_id = serializers.IntegerField(source="source_snapshot.id", read_only=True, allow_null=True)

    class Meta:
        model = AiContextDigest
        fields = (
            "id",
            "session_id",
            "from_message_id",
            "to_message_id",
            "source_snapshot_id",
            "summary",
            "risk_level",
            "facts_json",
            "excluded_facts_json",
            "asked_questions_json",
            "safety_notes_json",
            "message_count",
            "total_completed_messages",
            "estimated_input_tokens",
            "estimated_output_tokens",
            "estimated_cost",
            "provider",
            "model_name",
            "trigger_reason",
            "metadata_json",
            "created_at",
        )
        read_only_fields = fields


class AiSessionSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="case.id", read_only=True, allow_null=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True, allow_null=True)
    guest_session_id = serializers.UUIDField(source="guest_session.public_id", read_only=True, allow_null=True)
    message_count = serializers.SerializerMethodField()
    pending_assistant_messages = serializers.SerializerMethodField()
    latest_message_id = serializers.SerializerMethodField()
    latest_assistant_message_id = serializers.SerializerMethodField()
    latest_assistant_message_status = serializers.SerializerMethodField()

    class Meta:
        model = AiSession
        fields = (
            "id",
            "case_id",
            "user_id",
            "guest_session_id",
            "status",
            "started_at",
            "ended_at",
            "created_at",
            "updated_at",
            "message_count",
            "pending_assistant_messages",
            "latest_message_id",
            "latest_assistant_message_id",
            "latest_assistant_message_status",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField)
    def get_message_count(self, obj) -> int:
        return obj.messages.count()

    @extend_schema_field(serializers.IntegerField)
    def get_pending_assistant_messages(self, obj) -> int:
        return obj.messages.filter(
            role=AiMessage.Roles.ASSISTANT,
            status__in={AiMessage.Statuses.QUEUED, AiMessage.Statuses.PROCESSING},
        ).count()

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_latest_message_id(self, obj) -> int | None:
        latest_message = obj.messages.order_by("-created_at", "-id").first()
        return latest_message.id if latest_message is not None else None

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_latest_assistant_message_id(self, obj) -> int | None:
        latest_message = obj.messages.filter(role=AiMessage.Roles.ASSISTANT).order_by("-created_at", "-id").first()
        return latest_message.id if latest_message is not None else None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_latest_assistant_message_status(self, obj) -> str | None:
        latest_message = obj.messages.filter(role=AiMessage.Roles.ASSISTANT).order_by("-created_at", "-id").first()
        return latest_message.status if latest_message is not None else None


class AiSessionCreateSerializer(serializers.Serializer):
    case_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_case_id(self, value):
        if value is None:
            self.context["case"] = None
            return value

        request = self.context["request"]
        try:
            case = Case.objects.select_related("assigned_professional", "category", "current_diagnostic_node").get(id=value)
        except Case.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid case.") from exc

        if request.user.role == User.Roles.CUSTOMER and case.customer_user_id != request.user.id:
            raise serializers.ValidationError("You do not own this case.")
        if request.user.role == User.Roles.PROFESSIONAL and case.assigned_professional_id != request.user.id:
            raise serializers.ValidationError("You do not have access to this case.")

        self.context["case"] = case
        return value

    def create_or_reuse(self):
        user = self.context["request"].user
        case = self.context.get("case")
        session = AiSession.objects.filter(user=user, case=case, status=AiSession.Statuses.ACTIVE).first()
        created = False
        if session is None:
            session = AiSession.objects.create(user=user, case=case)
            created = True
        return session, created


class AiMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField()

    def validate_content(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Content cannot be empty.")
        return cleaned

    def validate(self, attrs):
        session = self.context["session"]
        if session.status != AiSession.Statuses.ACTIVE:
            raise serializers.ValidationError({"session": "Messages can be sent only to an active session."})
        if session.messages.filter(
            role=AiMessage.Roles.ASSISTANT,
            status__in={AiMessage.Statuses.QUEUED, AiMessage.Statuses.PROCESSING},
        ).exists():
            raise serializers.ValidationError(
                {"session": "An assistant reply is already pending for this session."}
            )

        request = self.context["request"]
        daily_limit = self.context["daily_limit"]
        today = timezone.localdate()
        used_messages = AiMessage.objects.filter(
            session__user=request.user,
            role=AiMessage.Roles.USER,
            created_at__date=today,
        ).count()
        if used_messages >= daily_limit:
            raise serializers.ValidationError({"limit": "Daily AI message limit reached."})

        try:
            enforce_ai_usage_limits(
                session,
                purpose="chat",
                estimated_input_tokens=estimate_token_count(attrs["content"]),
            )
        except AiUsageLimitExceeded as exc:
            raise serializers.ValidationError({"limit": str(exc)}) from exc

        return attrs


class AiDiagnosticTurnCreateSerializer(AiMessageCreateSerializer):
    diagnostic_chapter_id = serializers.IntegerField(required=False, allow_null=True)
    diagnostic_chapter_option_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        session = self.context["session"]
        if session.case_id is None:
            raise serializers.ValidationError({"case": "Diagnostic turns require a linked case."})
        if session.case.status in TERMINAL_CASE_STATUSES:
            raise serializers.ValidationError({"case": "Diagnostic turns cannot be added to a terminal case."})

        try:
            enforce_ai_usage_limits(
                session,
                purpose="diagnostic",
                estimated_input_tokens=estimate_token_count(attrs["content"]),
                check_case_turn_limit=True,
            )
        except AiUsageLimitExceeded as exc:
            raise serializers.ValidationError({"limit": str(exc)}) from exc

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

        self.context["diagnostic_chapter"] = chapter
        self.context["diagnostic_chapter_option"] = option
        return attrs


class AiMessagesQuerySerializer(serializers.Serializer):
    after_id = serializers.IntegerField(required=False, min_value=1)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)


class AiContextCompactSerializer(serializers.Serializer):
    force = serializers.BooleanField(required=False, default=True)
