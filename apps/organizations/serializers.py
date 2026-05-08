from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Organization, OrganizationMembership, OrganizationPlan
from .permissions import user_can_manage_organization
from .services import get_or_create_builtin_plan

User = get_user_model()


class OrganizationPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPlan
        fields = (
            "id",
            "slug",
            "name",
            "kind",
            "max_members",
            "can_open_cases",
            "can_manage_properties",
            "can_share_cases",
            "can_receive_cases",
            "can_accept_case_requests",
            "can_manage_members",
            "can_manage_billing",
            "can_view_all_org_cases",
            "can_use_ai_diagnostics",
            "is_active",
        )
        read_only_fields = fields


class OrganizationSerializer(serializers.ModelSerializer):
    plan = OrganizationPlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(source="plan.id", read_only=True)
    personal_owner_id = serializers.IntegerField(source="personal_owner.id", read_only=True, allow_null=True)
    created_by_user_id = serializers.IntegerField(source="created_by_user.id", read_only=True, allow_null=True)

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "kind",
            "status",
            "plan_id",
            "plan",
            "personal_owner_id",
            "created_by_user_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "kind")
        extra_kwargs = {"kind": {"required": False}}

    def validate_kind(self, value):
        if value != Organization.Kinds.PROFESSIONAL:
            raise serializers.ValidationError("Only professional organizations can be created from this endpoint.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        kind = validated_data.get("kind") or Organization.Kinds.PROFESSIONAL
        plan = get_or_create_builtin_plan(OrganizationPlan.Kinds.PROFESSIONAL)
        organization = Organization.objects.create(
            name=validated_data["name"],
            kind=kind,
            plan=plan,
            created_by_user=request.user,
        )
        OrganizationMembership.objects.create(
            user=request.user,
            organization=organization,
            role=OrganizationMembership.Roles.OWNER,
            scope=OrganizationMembership.Scopes.ORGANIZATION,
            status=OrganizationMembership.Statuses.ACTIVE,
            approved_by_user=request.user,
            approved_at=timezone.now(),
        )
        return organization


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)
    approved_by_user_id = serializers.IntegerField(source="approved_by_user.id", read_only=True, allow_null=True)

    class Meta:
        model = OrganizationMembership
        fields = (
            "id",
            "organization_id",
            "user_id",
            "user_email",
            "user_first_name",
            "user_last_name",
            "role",
            "scope",
            "status",
            "approved_by_user_id",
            "approved_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrganizationMembershipCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.Roles.choices)
    scope = serializers.ChoiceField(
        choices=OrganizationMembership.Scopes.choices,
        default=OrganizationMembership.Scopes.ASSIGNED,
    )

    def validate_email(self, value):
        normalized_email = User.objects.normalize_email(value)
        try:
            user = User.objects.get(email=normalized_email, is_active=True)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("No active user exists with this email.") from exc
        self.context["target_user"] = user
        return normalized_email

    def validate(self, attrs):
        organization = self.context["organization"]
        request = self.context["request"]
        target_user = self.context["target_user"]

        if not user_can_manage_organization(request.user, organization):
            raise serializers.ValidationError({"organization": "You cannot manage this organization."})

        if not organization.plan.can_manage_members:
            raise serializers.ValidationError({"organization": "This organization plan cannot manage members."})

        if OrganizationMembership.objects.filter(user=target_user, organization=organization).exists():
            raise serializers.ValidationError({"email": "This user is already a member of the organization."})

        active_members = OrganizationMembership.objects.filter(
            organization=organization,
            status=OrganizationMembership.Statuses.ACTIVE,
        ).count()
        if active_members >= organization.plan.max_members:
            raise serializers.ValidationError({"organization": "Organization member limit reached."})

        has_other_operational_membership = OrganizationMembership.objects.filter(
            user=target_user,
            status=OrganizationMembership.Statuses.ACTIVE,
        ).exclude(
            organization__kind=Organization.Kinds.PERSONAL,
        ).exclude(
            organization=organization,
        ).exists()
        if has_other_operational_membership and request.user.role != "admin":
            raise serializers.ValidationError(
                {"email": "Multi-organization operational memberships require platform approval."}
            )

        return attrs

    def create(self, validated_data):
        organization = self.context["organization"]
        request = self.context["request"]
        target_user = self.context["target_user"]
        return OrganizationMembership.objects.create(
            user=target_user,
            organization=organization,
            role=validated_data["role"],
            scope=validated_data["scope"],
            status=OrganizationMembership.Statuses.ACTIVE,
            approved_by_user=request.user,
            approved_at=timezone.now(),
        )

