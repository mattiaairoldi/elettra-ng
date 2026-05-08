from rest_framework import serializers

from .models import DiagnosticFlow, DiagnosticNode, DiagnosticOption


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
