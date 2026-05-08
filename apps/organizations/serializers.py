from django.contrib.auth import get_user_model
from django.db import transaction
from django.core import signing
from django.utils import timezone
from rest_framework import serializers

from .models import Organization, OrganizationInvitation, OrganizationMembership, OrganizationPlan
from .permissions import user_can_manage_organization
from .services import (
    build_invitation_expiry,
    count_active_members_and_pending_invitations,
    expire_invitation_if_needed,
    get_or_create_builtin_plan,
    normalize_invitation_email,
)
from .tokens import validate_organization_invitation_token

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


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    invited_by_user_id = serializers.IntegerField(source="invited_by_user.id", read_only=True, allow_null=True)
    accepted_by_user_id = serializers.IntegerField(source="accepted_by_user.id", read_only=True, allow_null=True)
    accepted_membership_id = serializers.IntegerField(source="accepted_membership.id", read_only=True, allow_null=True)
    revoked_by_user_id = serializers.IntegerField(source="revoked_by_user.id", read_only=True, allow_null=True)

    class Meta:
        model = OrganizationInvitation
        fields = (
            "id",
            "organization_id",
            "email",
            "role",
            "scope",
            "status",
            "invited_by_user_id",
            "accepted_by_user_id",
            "accepted_membership_id",
            "revoked_by_user_id",
            "expires_at",
            "accepted_at",
            "revoked_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrganizationInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.Roles.choices)
    scope = serializers.ChoiceField(
        choices=OrganizationMembership.Scopes.choices,
        default=OrganizationMembership.Scopes.ASSIGNED,
    )

    def validate_email(self, value):
        return normalize_invitation_email(value)

    def validate(self, attrs):
        organization = self.context["organization"]
        request = self.context["request"]
        email = attrs["email"]

        if not user_can_manage_organization(request.user, organization):
            raise serializers.ValidationError({"organization": "You cannot manage this organization."})

        if not organization.plan.can_manage_members:
            raise serializers.ValidationError({"organization": "This organization plan cannot manage members."})

        if count_active_members_and_pending_invitations(organization) >= organization.plan.max_members:
            raise serializers.ValidationError({"organization": "Organization member limit reached."})

        existing_user = User.objects.filter(email=email, is_active=True).first()
        if existing_user is not None:
            if OrganizationMembership.objects.filter(user=existing_user, organization=organization).exists():
                raise serializers.ValidationError({"email": "This user is already a member of the organization."})

            has_other_operational_membership = OrganizationMembership.objects.filter(
                user=existing_user,
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

        if OrganizationInvitation.objects.filter(
            organization=organization,
            email=email,
            status=OrganizationInvitation.Statuses.PENDING,
            expires_at__gt=timezone.now(),
        ).exists():
            raise serializers.ValidationError({"email": "A pending invitation already exists for this email."})

        return attrs

    def create(self, validated_data):
        organization = self.context["organization"]
        request = self.context["request"]
        return OrganizationInvitation.objects.create(
            organization=organization,
            email=validated_data["email"],
            role=validated_data["role"],
            scope=validated_data["scope"],
            status=OrganizationInvitation.Statuses.PENDING,
            invited_by_user=request.user,
            expires_at=build_invitation_expiry(),
        )


class OrganizationInvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        request = self.context["request"]
        try:
            payload = validate_organization_invitation_token(attrs["token"])
        except signing.BadSignature as exc:
            raise serializers.ValidationError({"token": "Invalid invitation token."}) from exc

        invitation = (
            OrganizationInvitation.objects.select_related("organization", "organization__plan")
            .filter(id=payload.get("invitation_id"), email=payload.get("email"))
            .first()
        )
        if invitation is None:
            raise serializers.ValidationError({"token": "Invalid invitation token."})
        if expire_invitation_if_needed(invitation):
            raise serializers.ValidationError({"token": "Invitation expired."})
        if invitation.status != OrganizationInvitation.Statuses.PENDING:
            raise serializers.ValidationError({"token": "Invitation is not pending."})
        if request.user.email.lower() != invitation.email.lower():
            raise serializers.ValidationError({"token": "Invitation email does not match current user."})
        if OrganizationMembership.objects.filter(user=request.user, organization=invitation.organization).exists():
            raise serializers.ValidationError({"token": "Current user is already a member of the organization."})
        active_members = OrganizationMembership.objects.filter(
            organization=invitation.organization,
            status=OrganizationMembership.Statuses.ACTIVE,
        ).count()
        if active_members >= invitation.organization.plan.max_members:
            raise serializers.ValidationError({"organization": "Organization member limit reached."})

        has_other_operational_membership = OrganizationMembership.objects.filter(
            user=request.user,
            status=OrganizationMembership.Statuses.ACTIVE,
        ).exclude(
            organization__kind=Organization.Kinds.PERSONAL,
        ).exclude(
            organization=invitation.organization,
        ).exists()
        if has_other_operational_membership and invitation.invited_by_user and invitation.invited_by_user.role != "admin":
            raise serializers.ValidationError(
                {"token": "Multi-organization operational memberships require platform approval."}
            )

        attrs["invitation"] = invitation
        return attrs

    @transaction.atomic
    def save(self):
        request = self.context["request"]
        invitation = self.validated_data["invitation"]
        membership = OrganizationMembership.objects.create(
            user=request.user,
            organization=invitation.organization,
            role=invitation.role,
            scope=invitation.scope,
            status=OrganizationMembership.Statuses.ACTIVE,
            approved_by_user=invitation.invited_by_user,
            approved_at=timezone.now(),
        )
        invitation.status = OrganizationInvitation.Statuses.ACCEPTED
        invitation.accepted_by_user = request.user
        invitation.accepted_membership = membership
        invitation.accepted_at = timezone.now()
        invitation.save(
            update_fields=[
                "status",
                "accepted_by_user",
                "accepted_membership",
                "accepted_at",
                "updated_at",
            ]
        )
        return invitation, membership
