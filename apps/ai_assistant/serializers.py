from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.cases.models import Case
from apps.identity.models import User

from .models import AiDiagnosticSnapshot, AiMessage, AiSession


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

    class Meta:
        model = AiDiagnosticSnapshot
        fields = (
            "id",
            "session_id",
            "source_message_id",
            "summary",
            "risk_level",
            "next_question",
            "escalation_recommended",
            "escalation_reason",
            "recommendation",
            "facts_json",
            "safety_notes_json",
            "raw_payload_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AiSessionSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="case.id", read_only=True, allow_null=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
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

        return attrs


class AiDiagnosticTurnCreateSerializer(AiMessageCreateSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        session = self.context["session"]
        if session.case_id is None:
            raise serializers.ValidationError({"case": "Diagnostic turns require a linked case."})
        if session.case.status in TERMINAL_CASE_STATUSES:
            raise serializers.ValidationError({"case": "Diagnostic turns cannot be added to a terminal case."})
        return attrs


class AiMessagesQuerySerializer(serializers.Serializer):
    after_id = serializers.IntegerField(required=False, min_value=1)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)
