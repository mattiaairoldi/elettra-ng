from rest_framework import serializers

from apps.common.serializers import GeoPointField
from apps.identity.models import User
from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.services import (
    get_or_create_personal_organization,
    user_has_active_organization_membership,
)
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticFlow, DiagnosticNode, DiagnosticOption

from .models import (
    Asset,
    AssetMaintenanceEvent,
    AssetMaintenanceReminder,
    Case,
    CaseEvent,
    CaseNote,
    CaseShareRequest,
    Property,
)


CASE_STATUS_TRANSITIONS = {
    Case.Statuses.OPEN: {
        Case.Statuses.IN_DIAGNOSIS,
        Case.Statuses.WAITING_PROFESSIONAL,
        Case.Statuses.CANCELLED,
    },
    Case.Statuses.IN_DIAGNOSIS: {
        Case.Statuses.WAITING_PROFESSIONAL,
        Case.Statuses.SCHEDULED,
        Case.Statuses.RESOLVED,
        Case.Statuses.CANCELLED,
    },
    Case.Statuses.WAITING_PROFESSIONAL: {
        Case.Statuses.IN_DIAGNOSIS,
        Case.Statuses.SCHEDULED,
        Case.Statuses.CANCELLED,
    },
    Case.Statuses.SCHEDULED: {
        Case.Statuses.IN_DIAGNOSIS,
        Case.Statuses.RESOLVED,
        Case.Statuses.CANCELLED,
    },
    Case.Statuses.RESOLVED: {
        Case.Statuses.CLOSED,
    },
    Case.Statuses.CLOSED: set(),
    Case.Statuses.CANCELLED: set(),
}

TERMINAL_CASE_STATUSES = {
    Case.Statuses.RESOLVED,
    Case.Statuses.CLOSED,
    Case.Statuses.CANCELLED,
}


def resolve_asset_property_links(attrs, *, instance, request):
    asset_id_explicit = "asset_id" in attrs
    property_id_explicit = "property_id" in attrs

    asset_obj = instance.asset if instance is not None else None
    property_obj = instance.property if instance is not None else None

    if property_id_explicit:
        property_id = attrs.get("property_id")
        if property_id is None:
            property_obj = None
        else:
            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist as exc:
                raise serializers.ValidationError({"property_id": "Invalid property."}) from exc
            if not user_has_active_organization_membership(request.user, property_obj.organization_id):
                raise serializers.ValidationError({"property_id": "You do not own this property."})

    if asset_id_explicit:
        asset_id = attrs.get("asset_id")
        if asset_id is None:
            asset_obj = None
        else:
            try:
                asset_obj = Asset.objects.select_related("property", "property__organization").get(id=asset_id)
            except Asset.DoesNotExist as exc:
                raise serializers.ValidationError({"asset_id": "Invalid asset."}) from exc
            if not user_has_active_organization_membership(request.user, asset_obj.property.organization_id):
                raise serializers.ValidationError({"asset_id": "You do not own this asset."})

    if asset_obj is not None and property_obj is None:
        property_obj = asset_obj.property

    if asset_obj is not None and property_obj is not None and asset_obj.property_id != property_obj.id:
        raise serializers.ValidationError({"asset_id": "Asset does not belong to the selected property."})

    if asset_obj is None and property_obj is None:
        raise serializers.ValidationError("At least one between asset_id and property_id is required.")

    return asset_obj, property_obj


class PropertySerializer(serializers.ModelSerializer):
    owner_user_id = serializers.IntegerField(source="owner_user.id", read_only=True)
    organization_id = serializers.IntegerField(read_only=True)
    location = GeoPointField(required=False, allow_null=True)

    class Meta:
        model = Property
        fields = (
            "id",
            "owner_user_id",
            "organization_id",
            "name",
            "address_text",
            "city",
            "location",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner_user_id", "organization_id", "created_at", "updated_at")


class AssetSerializer(serializers.ModelSerializer):
    property_id = serializers.IntegerField()
    category_id = serializers.IntegerField()
    location = GeoPointField(required=False, allow_null=True)

    class Meta:
        model = Asset
        fields = (
            "id",
            "property_id",
            "category_id",
            "name",
            "description",
            "location_text",
            "location",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_property_id(self, value):
        request = self.context["request"]
        try:
            property_obj = Property.objects.get(id=value)
        except Property.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid property.") from exc
        if not user_has_active_organization_membership(request.user, property_obj.organization_id):
            raise serializers.ValidationError("You do not own this property.")
        self.context["property_obj"] = property_obj
        return value

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid category.")
        return value

    def create(self, validated_data):
        validated_data["property"] = self.context["property_obj"]
        validated_data["category_id"] = validated_data.pop("category_id")
        validated_data.pop("property_id")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "property_id" in validated_data:
            instance.property = self.context["property_obj"]
            validated_data.pop("property_id")
        if "category_id" in validated_data:
            instance.category_id = validated_data.pop("category_id")
        return super().update(instance, validated_data)


class AssetMaintenanceEventSerializer(serializers.ModelSerializer):
    asset_id = serializers.IntegerField(required=False, allow_null=True)
    property_id = serializers.IntegerField(required=False, allow_null=True)
    created_by_user_id = serializers.IntegerField(source="created_by_user.id", read_only=True, allow_null=True)

    class Meta:
        model = AssetMaintenanceEvent
        fields = (
            "id",
            "asset_id",
            "property_id",
            "event_type",
            "title",
            "description",
            "event_date",
            "cost_amount",
            "metadata_json",
            "created_by_user_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by_user_id", "created_at", "updated_at")

    def validate(self, attrs):
        asset_obj, property_obj = resolve_asset_property_links(
            attrs,
            instance=self.instance,
            request=self.context["request"],
        )
        attrs["asset"] = asset_obj
        attrs["property"] = property_obj
        return attrs

    def create(self, validated_data):
        validated_data["created_by_user"] = self.context["request"].user
        validated_data["asset"] = validated_data.pop("asset")
        validated_data["property"] = validated_data.pop("property")
        validated_data.pop("asset_id", None)
        validated_data.pop("property_id", None)
        return AssetMaintenanceEvent.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "asset" in validated_data:
            instance.asset = validated_data.pop("asset")
        if "property" in validated_data:
            instance.property = validated_data.pop("property")
        validated_data.pop("asset_id", None)
        validated_data.pop("property_id", None)
        return super().update(instance, validated_data)


class AssetMaintenanceReminderSerializer(serializers.ModelSerializer):
    asset_id = serializers.IntegerField(required=False, allow_null=True)
    property_id = serializers.IntegerField(required=False, allow_null=True)
    created_by_user_id = serializers.IntegerField(source="created_by_user.id", read_only=True, allow_null=True)

    class Meta:
        model = AssetMaintenanceReminder
        fields = (
            "id",
            "asset_id",
            "property_id",
            "title",
            "description",
            "due_at",
            "recurrence_rule",
            "recurrence_custom",
            "status",
            "last_completed_at",
            "metadata_json",
            "created_by_user_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "last_completed_at", "created_by_user_id", "created_at", "updated_at")

    def validate(self, attrs):
        asset_obj, property_obj = resolve_asset_property_links(
            attrs,
            instance=self.instance,
            request=self.context["request"],
        )
        attrs["asset"] = asset_obj
        attrs["property"] = property_obj
        return attrs

    def create(self, validated_data):
        validated_data["created_by_user"] = self.context["request"].user
        validated_data["asset"] = validated_data.pop("asset")
        validated_data["property"] = validated_data.pop("property")
        validated_data.pop("asset_id", None)
        validated_data.pop("property_id", None)
        return AssetMaintenanceReminder.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "asset" in validated_data:
            instance.asset = validated_data.pop("asset")
        if "property" in validated_data:
            instance.property = validated_data.pop("property")
        validated_data.pop("asset_id", None)
        validated_data.pop("property_id", None)
        return super().update(instance, validated_data)


class CaseSerializer(serializers.ModelSerializer):
    customer_user_id = serializers.IntegerField(source="customer_user.id", read_only=True)
    owner_organization_id = serializers.IntegerField(read_only=True)
    assigned_professional_id = serializers.IntegerField(source="assigned_professional.id", read_only=True, allow_null=True)
    category_id = serializers.IntegerField(read_only=True)
    property_id = serializers.IntegerField(read_only=True, allow_null=True)
    asset_id = serializers.IntegerField(read_only=True, allow_null=True)
    troubleshooting_flow_id = serializers.IntegerField(source="troubleshooting_flow.id", read_only=True, allow_null=True)
    current_diagnostic_node_id = serializers.IntegerField(source="current_diagnostic_node.id", read_only=True, allow_null=True)

    class Meta:
        model = Case
        fields = (
            "id",
            "customer_user_id",
            "owner_organization_id",
            "assigned_professional_id",
            "category_id",
            "property_id",
            "asset_id",
            "troubleshooting_flow_id",
            "current_diagnostic_node_id",
            "title",
            "description",
            "status",
            "priority",
            "source",
            "opened_at",
            "closed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CaseWriteSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField()
    property_id = serializers.IntegerField(required=False, allow_null=True)
    asset_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Case
        fields = ("category_id", "property_id", "asset_id", "title", "description", "priority")

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid category.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        instance = self.instance

        if instance is not None and request.user.role == User.Roles.PROFESSIONAL:
            raise serializers.ValidationError("Professionals cannot update case details.")

        property_id_explicit = "property_id" in attrs
        asset_id_explicit = "asset_id" in attrs

        property_obj = instance.property if instance is not None else None
        asset_obj = instance.asset if instance is not None else None

        if property_id_explicit:
            property_id = attrs.get("property_id")
            if property_id is None:
                property_obj = None
            else:
                try:
                    property_obj = Property.objects.get(id=property_id)
                except Property.DoesNotExist as exc:
                    raise serializers.ValidationError({"property_id": "Invalid property."}) from exc
                if not user_has_active_organization_membership(request.user, property_obj.organization_id):
                    raise serializers.ValidationError({"property_id": "You do not own this property."})

        if asset_id_explicit:
            asset_id = attrs.get("asset_id")
            if asset_id is None:
                asset_obj = None
            else:
                try:
                    asset_obj = Asset.objects.select_related("property").get(id=asset_id)
                except Asset.DoesNotExist as exc:
                    raise serializers.ValidationError({"asset_id": "Invalid asset."}) from exc
                if not user_has_active_organization_membership(request.user, asset_obj.property.organization_id):
                    raise serializers.ValidationError({"asset_id": "You do not own this asset."})

        if asset_obj is not None and property_id_explicit and property_obj is None:
            raise serializers.ValidationError({"property_id": "Property cannot be empty when an asset is selected."})

        if asset_obj is not None and property_obj is None:
            property_obj = asset_obj.property

        if asset_obj is not None and property_obj is not None and asset_obj.property_id != property_obj.id:
            raise serializers.ValidationError({"asset_id": "Asset does not belong to the selected property."})

        owner_organization = instance.owner_organization if instance is not None else None
        if owner_organization is None:
            owner_organization = property_obj.organization if property_obj is not None else get_or_create_personal_organization(request.user)
        if property_obj is not None and property_obj.organization_id != owner_organization.id:
            raise serializers.ValidationError({"property_id": "Property does not belong to the case owner organization."})

        if instance is not None and instance.troubleshooting_flow_id is not None:
            next_category_id = attrs.get("category_id", instance.category_id)
            if next_category_id != instance.category_id:
                raise serializers.ValidationError({"category_id": "Cannot change category after troubleshooting has started."})

        if instance is not None and instance.appointments.exists():
            if (property_obj.id if property_obj is not None else None) != instance.property_id:
                raise serializers.ValidationError({"property_id": "Cannot change property after appointments exist."})
            if (asset_obj.id if asset_obj is not None else None) != instance.asset_id:
                raise serializers.ValidationError({"asset_id": "Cannot change asset after appointments exist."})
            if attrs.get("category_id", instance.category_id) != instance.category_id:
                raise serializers.ValidationError({"category_id": "Cannot change category after appointments exist."})

        attrs["property"] = property_obj
        attrs["asset"] = asset_obj
        attrs["owner_organization"] = owner_organization
        return attrs

    def create(self, validated_data):
        validated_data["customer_user"] = self.context["request"].user
        validated_data["owner_organization"] = validated_data.pop("owner_organization")
        validated_data["category_id"] = validated_data.pop("category_id")
        validated_data["property"] = validated_data.pop("property", None)
        validated_data["asset"] = validated_data.pop("asset", None)
        validated_data.pop("property_id", None)
        validated_data.pop("asset_id", None)
        return Case.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "category_id" in validated_data:
            instance.category_id = validated_data.pop("category_id")
        if "property" in validated_data:
            instance.property = validated_data.pop("property")
        if "asset" in validated_data:
            instance.asset = validated_data.pop("asset")
        validated_data.pop("owner_organization", None)
        validated_data.pop("property_id", None)
        validated_data.pop("asset_id", None)
        return super().update(instance, validated_data)


class CaseStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Case.Statuses.choices)

    def validate(self, attrs):
        case = self.context["case"]
        request = self.context["request"]
        next_status = attrs["status"]

        if next_status == case.status:
            return attrs

        if next_status == Case.Statuses.SCHEDULED and case.assigned_professional_id is None:
            raise serializers.ValidationError({"status": "A case must be assigned before it can be scheduled."})

        if request.user.role == User.Roles.CUSTOMER:
            allowed_statuses = {Case.Statuses.CANCELLED}
            if case.status == Case.Statuses.RESOLVED:
                allowed_statuses.add(Case.Statuses.CLOSED)
            if next_status not in allowed_statuses:
                raise serializers.ValidationError(
                    {"status": "Customers can only cancel a case or close a resolved one."}
                )
        elif request.user.role == User.Roles.PROFESSIONAL:
            allowed_statuses = {
                Case.Statuses.IN_DIAGNOSIS,
                Case.Statuses.WAITING_PROFESSIONAL,
                Case.Statuses.SCHEDULED,
                Case.Statuses.RESOLVED,
            }
            if next_status not in allowed_statuses:
                raise serializers.ValidationError(
                    {"status": "Professionals cannot set this case status."}
                )

        if next_status not in CASE_STATUS_TRANSITIONS[case.status]:
            raise serializers.ValidationError({"status": "Invalid status transition for this case."})

        return attrs


class CaseAssignSerializer(serializers.Serializer):
    professional_user_id = serializers.IntegerField(allow_null=True, required=False)

    def validate_professional_user_id(self, value):
        if value is None:
            return value
        try:
            user = User.objects.get(id=value, is_active=True)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid professional user.") from exc
        if user.role != User.Roles.PROFESSIONAL:
            raise serializers.ValidationError("Assigned user must have professional role.")
        self.context["professional_user"] = user
        return value


class CaseShareRequestSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="case.id", read_only=True)
    requester_user_id = serializers.IntegerField(source="requester_user.id", read_only=True)
    recipient_organization_id = serializers.IntegerField(source="recipient_organization.id", read_only=True)
    recipient_membership_id = serializers.IntegerField(source="recipient_membership.id", read_only=True, allow_null=True)
    accepted_by_user_id = serializers.IntegerField(source="accepted_by_user.id", read_only=True, allow_null=True)
    rejected_by_user_id = serializers.IntegerField(source="rejected_by_user.id", read_only=True, allow_null=True)
    revoked_by_user_id = serializers.IntegerField(source="revoked_by_user.id", read_only=True, allow_null=True)
    conversation_id = serializers.IntegerField(source="conversation.id", read_only=True, allow_null=True)

    class Meta:
        model = CaseShareRequest
        fields = (
            "id",
            "case_id",
            "requester_user_id",
            "recipient_organization_id",
            "recipient_membership_id",
            "status",
            "share_scope",
            "visible_title",
            "visible_summary",
            "shared_payload_json",
            "rejection_reason",
            "accepted_by_user_id",
            "accepted_at",
            "rejected_by_user_id",
            "rejected_at",
            "revoked_by_user_id",
            "revoked_at",
            "conversation_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CaseShareRequestCreateSerializer(serializers.ModelSerializer):
    recipient_organization_id = serializers.IntegerField()
    recipient_membership_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = CaseShareRequest
        fields = (
            "recipient_organization_id",
            "recipient_membership_id",
            "share_scope",
            "visible_title",
            "visible_summary",
            "shared_payload_json",
        )
        extra_kwargs = {
            "visible_title": {"required": False, "allow_blank": True},
            "visible_summary": {"required": False, "allow_blank": True},
            "shared_payload_json": {"required": False},
            "share_scope": {"required": False},
        }

    def validate(self, attrs):
        case = self.context["case"]
        recipient_organization_id = attrs["recipient_organization_id"]
        recipient_membership_id = attrs.get("recipient_membership_id")

        try:
            recipient_organization = Organization.objects.select_related("plan").get(
                id=recipient_organization_id,
                status=Organization.Statuses.ACTIVE,
            )
        except Organization.DoesNotExist as exc:
            raise serializers.ValidationError({"recipient_organization_id": "Invalid recipient organization."}) from exc

        if recipient_organization.id == case.owner_organization_id:
            raise serializers.ValidationError({"recipient_organization_id": "Cannot share a case with its owner organization."})

        if not recipient_organization.plan.can_receive_cases:
            raise serializers.ValidationError({"recipient_organization_id": "Recipient organization cannot receive cases."})

        recipient_membership = None
        if recipient_membership_id is not None:
            try:
                recipient_membership = OrganizationMembership.objects.select_related("user", "organization").get(
                    id=recipient_membership_id,
                    organization=recipient_organization,
                    status=OrganizationMembership.Statuses.ACTIVE,
                )
            except OrganizationMembership.DoesNotExist as exc:
                raise serializers.ValidationError({"recipient_membership_id": "Invalid recipient membership."}) from exc

        visible_title = attrs.get("visible_title", "").strip() or case.title
        visible_summary = attrs.get("visible_summary", "").strip() or case.description

        attrs["recipient_organization"] = recipient_organization
        attrs["recipient_membership"] = recipient_membership
        attrs["visible_title"] = visible_title
        attrs["visible_summary"] = visible_summary
        attrs["shared_payload_json"] = attrs.get("shared_payload_json") or {}
        return attrs

    def create(self, validated_data):
        case = self.context["case"]
        request = self.context["request"]
        validated_data.pop("recipient_organization_id")
        validated_data.pop("recipient_membership_id", None)
        return CaseShareRequest.objects.create(
            case=case,
            requester_user=request.user,
            **validated_data,
        )


class CaseShareRequestRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class CaseNoteSerializer(serializers.ModelSerializer):
    author_user_id = serializers.IntegerField(source="author_user.id", read_only=True)
    case_id = serializers.IntegerField(source="case.id", read_only=True)

    class Meta:
        model = CaseNote
        fields = ("id", "case_id", "author_user_id", "note_type", "body", "is_internal", "created_at", "updated_at")
        read_only_fields = ("id", "case_id", "author_user_id", "created_at", "updated_at")
        extra_kwargs = {"note_type": {"required": False}}

    def validate(self, attrs):
        request = self.context["request"]
        if attrs.get("is_internal") and request.user.role == "customer":
            raise serializers.ValidationError({"is_internal": "Customers cannot create internal notes."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        case = self.context["case"]
        if "note_type" not in validated_data:
            if request.user.role == "professional":
                validated_data["note_type"] = CaseNote.NoteTypes.PROFESSIONAL
            elif request.user.role == "admin":
                validated_data["note_type"] = CaseNote.NoteTypes.OPERATOR
            else:
                validated_data["note_type"] = CaseNote.NoteTypes.CUSTOMER
        return CaseNote.objects.create(case=case, author_user=request.user, **validated_data)


class CaseEventSerializer(serializers.ModelSerializer):
    actor_user_id = serializers.IntegerField(source="actor_user.id", read_only=True, allow_null=True)
    case_id = serializers.IntegerField(source="case.id", read_only=True)

    class Meta:
        model = CaseEvent
        fields = ("id", "case_id", "event_type", "actor_user_id", "payload_json", "created_at")
        read_only_fields = fields


class CaseTroubleshootingStartSerializer(serializers.Serializer):
    flow_id = serializers.IntegerField()

    def validate_flow_id(self, value):
        case = self.context["case"]
        try:
            flow = DiagnosticFlow.objects.get(id=value, status=DiagnosticFlow.Statuses.PUBLISHED, is_public=True)
        except DiagnosticFlow.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid flow.") from exc
        if flow.category_id != case.category_id:
            raise serializers.ValidationError("Flow category does not match the case category.")
        if case.status in TERMINAL_CASE_STATUSES:
            raise serializers.ValidationError("Troubleshooting cannot be started on a terminal case.")
        self.context["flow"] = flow
        return value


class CaseTroubleshootingProgressSerializer(serializers.Serializer):
    node_id = serializers.IntegerField()
    option_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        case = self.context["case"]
        if case.troubleshooting_flow_id is None:
            raise serializers.ValidationError({"flow_id": "Troubleshooting has not been started for this case."})
        if case.status != Case.Statuses.IN_DIAGNOSIS:
            raise serializers.ValidationError({"status": "Troubleshooting can progress only while the case is in diagnosis."})
        try:
            node = DiagnosticNode.objects.get(id=attrs["node_id"], flow=case.troubleshooting_flow)
        except DiagnosticNode.DoesNotExist as exc:
            raise serializers.ValidationError({"node_id": "Invalid node for this case flow."}) from exc
        if case.current_diagnostic_node_id is not None and case.current_diagnostic_node_id != node.id:
            raise serializers.ValidationError({"node_id": "Node does not match the current troubleshooting position."})
        attrs["node"] = node

        option_id = attrs.get("option_id")
        if option_id is not None:
            try:
                option = DiagnosticOption.objects.get(id=option_id, from_node=node)
            except DiagnosticOption.DoesNotExist as exc:
                raise serializers.ValidationError({"option_id": "Invalid option for this node."}) from exc
            attrs["option"] = option
        elif node.options.exists():
            raise serializers.ValidationError({"option_id": "Option is required for this node."})
        return attrs
