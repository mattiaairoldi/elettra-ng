from rest_framework import serializers

from apps.cases.models import Asset, Case
from apps.cases.events import TERMINAL_CASE_STATUSES
from apps.organizations.services import user_has_active_organization_membership

from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_user_id = serializers.IntegerField(source="uploaded_by_user.id", read_only=True)
    case_id = serializers.IntegerField(source="case.id", read_only=True, allow_null=True)
    asset_id = serializers.IntegerField(source="asset.id", read_only=True, allow_null=True)
    file_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = Attachment
        fields = (
            "id",
            "uploaded_by_user_id",
            "case_id",
            "asset_id",
            "file_url",
            "file_name",
            "mime_type",
            "size_bytes",
            "attachment_type",
            "created_at",
        )
        read_only_fields = fields


class AttachmentUploadSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(required=False, allow_null=True)
    asset_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Attachment
        fields = ("file", "case_id", "asset_id", "attachment_type")

    def validate(self, attrs):
        request = self.context["request"]
        case_id = attrs.get("case_id")
        asset_id = attrs.get("asset_id")

        if case_id is None and asset_id is None:
            raise serializers.ValidationError("At least one between case_id and asset_id is required.")

        case = None
        asset = None

        if case_id is not None:
            try:
                case = Case.objects.get(id=case_id)
            except Case.DoesNotExist as exc:
                raise serializers.ValidationError({"case_id": "Invalid case."}) from exc
            if case.status in TERMINAL_CASE_STATUSES:
                raise serializers.ValidationError({"case_id": "Attachments cannot be uploaded for a terminal case."})
            if request.user.role == "customer" and case.customer_user_id != request.user.id:
                raise serializers.ValidationError({"case_id": "You do not own this case."})
            if request.user.role == "professional" and case.assigned_professional_id != request.user.id:
                raise serializers.ValidationError({"case_id": "You do not have access to this case."})

        if asset_id is not None:
            try:
                asset = Asset.objects.select_related("property").get(id=asset_id)
            except Asset.DoesNotExist as exc:
                raise serializers.ValidationError({"asset_id": "Invalid asset."}) from exc
            has_asset_membership = user_has_active_organization_membership(
                request.user,
                asset.property.organization_id,
            )
            if not has_asset_membership and request.user.role != "professional":
                raise serializers.ValidationError({"asset_id": "You do not have access to this asset."})
            if not has_asset_membership and request.user.role == "professional":
                if case is None or case.assigned_professional_id != request.user.id:
                    raise serializers.ValidationError({"asset_id": "You do not have access to this asset."})
                if case.asset_id is not None and case.asset_id != asset.id:
                    raise serializers.ValidationError({"asset_id": "Asset does not match the selected case."})

        if case is not None and asset is not None:
            if case.asset_id is not None and case.asset_id != asset.id:
                raise serializers.ValidationError({"asset_id": "Asset does not match the selected case."})
            if case.property_id is not None and asset.property_id != case.property_id:
                raise serializers.ValidationError({"asset_id": "Asset does not belong to the selected case property."})

        attrs["case"] = case
        attrs["asset"] = asset
        return attrs

    def create(self, validated_data):
        uploaded_file = validated_data["file"]
        validated_data["uploaded_by_user"] = self.context["request"].user
        validated_data["file_name"] = uploaded_file.name
        validated_data["mime_type"] = getattr(uploaded_file, "content_type", "") or ""
        validated_data["size_bytes"] = uploaded_file.size
        validated_data.pop("case_id", None)
        validated_data.pop("asset_id", None)
        return Attachment.objects.create(**validated_data)
