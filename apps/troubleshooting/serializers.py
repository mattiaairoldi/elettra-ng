from rest_framework import serializers

from apps.cases.events import create_case_event, update_case_status
from apps.cases.models import Case, CaseEvent
from apps.identity.models import User

from .models import (
    DiagnosticAdviceStep,
    DiagnosticChapter,
    DiagnosticChapterOption,
    DiagnosticFlow,
    DiagnosticNode,
    DiagnosticOption,
    DiagnosticSafetyRule,
)


class DiagnosticSafetyRuleSerializer(serializers.ModelSerializer):
    chapter_id = serializers.IntegerField(source="chapter.id", read_only=True)

    class Meta:
        model = DiagnosticSafetyRule
        fields = (
            "id",
            "chapter_id",
            "title",
            "trigger_terms_json",
            "guidance",
            "risk_level",
            "escalation_level",
            "sort_order",
            "is_active",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DiagnosticAdviceStepSerializer(serializers.ModelSerializer):
    chapter_id = serializers.IntegerField(source="chapter.id", read_only=True)
    chapter_option_id = serializers.IntegerField(source="chapter_option.id", read_only=True, allow_null=True)

    class Meta:
        model = DiagnosticAdviceStep
        fields = (
            "id",
            "chapter_id",
            "chapter_option_id",
            "title",
            "slug",
            "body",
            "step_type",
            "safety_level",
            "resolution_prompt",
            "next_actions_json",
            "sort_order",
            "is_active",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DiagnosticAdviceFeedbackSerializer(serializers.Serializer):
    case_id = serializers.IntegerField()
    resolved = serializers.BooleanField()
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate_case_id(self, value):
        request = self.context["request"]
        try:
            case = Case.objects.select_related("customer_user", "assigned_professional", "category").get(id=value)
        except Case.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid case.") from exc

        if request.user.role == User.Roles.CUSTOMER and case.customer_user_id != request.user.id:
            raise serializers.ValidationError("You do not own this case.")
        if request.user.role == User.Roles.PROFESSIONAL and case.assigned_professional_id != request.user.id:
            raise serializers.ValidationError("You do not have access to this case.")

        self.context["case"] = case
        return value

    def save_feedback(self):
        request = self.context["request"]
        step = self.context["advice_step"]
        case = self.context["case"]
        resolved = self.validated_data["resolved"]
        note = self.validated_data.get("note", "").strip()
        previous_status = case.status

        if resolved:
            update_case_status(
                case,
                Case.Statuses.RESOLVED,
                actor_user=request.user,
                payload={
                    "diagnostic_advice_step_id": step.id,
                    "previous_status": previous_status,
                    "source": "diagnostic_advice_feedback",
                },
            )
        elif case.status == Case.Statuses.OPEN:
            update_case_status(
                case,
                Case.Statuses.IN_DIAGNOSIS,
                actor_user=request.user,
                payload={
                    "diagnostic_advice_step_id": step.id,
                    "previous_status": previous_status,
                    "source": "diagnostic_advice_feedback",
                },
            )
            case.refresh_from_db()

        next_actions = [] if resolved else step.next_actions_json
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.TROUBLESHOOTING_PROGRESS,
            actor_user=request.user,
            payload={
                "diagnostic_advice_step_id": step.id,
                "resolved": resolved,
                "note": note,
                "previous_status": previous_status,
                "status": case.status,
                "next_actions": next_actions,
            },
        )
        return {
            "case_id": case.id,
            "resolved": resolved,
            "case_status": case.status,
            "next_actions": next_actions,
        }


class DiagnosticChapterOptionSerializer(serializers.ModelSerializer):
    chapter_id = serializers.IntegerField(source="chapter.id", read_only=True)

    class Meta:
        model = DiagnosticChapterOption
        fields = (
            "id",
            "chapter_id",
            "label",
            "slug",
            "description",
            "option_type",
            "prompt_hint",
            "sort_order",
            "is_active",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DiagnosticChapterSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source="category.id", read_only=True, allow_null=True)
    options = DiagnosticChapterOptionSerializer(many=True, read_only=True)
    safety_rules = DiagnosticSafetyRuleSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticChapter
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category_id",
            "prompt_context",
            "safety_context",
            "status",
            "is_public",
            "sort_order",
            "metadata_json",
            "options",
            "safety_rules",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DiagnosticFlowSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source="category.id", read_only=True)

    class Meta:
        model = DiagnosticFlow
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "category_id",
            "status",
            "version",
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DiagnosticNodeSerializer(serializers.ModelSerializer):
    flow_id = serializers.IntegerField(source="flow.id", read_only=True)

    class Meta:
        model = DiagnosticNode
        fields = (
            "id",
            "flow_id",
            "title",
            "body",
            "node_type",
            "sort_order",
            "is_entrypoint",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DiagnosticOptionSerializer(serializers.ModelSerializer):
    from_node_id = serializers.IntegerField(source="from_node.id", read_only=True)
    to_node_id = serializers.IntegerField(source="to_node.id", read_only=True, allow_null=True)

    class Meta:
        model = DiagnosticOption
        fields = (
            "id",
            "from_node_id",
            "to_node_id",
            "label",
            "sort_order",
            "is_default",
            "metadata_json",
        )
        read_only_fields = fields
