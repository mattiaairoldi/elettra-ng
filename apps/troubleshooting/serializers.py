from rest_framework import serializers

from .models import (
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
