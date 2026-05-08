from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Organization, OrganizationInvitation, OrganizationMembership, OrganizationPlan
from .tokens import validate_organization_invitation_token


BUILTIN_PLAN_DEFINITIONS = {
    OrganizationPlan.Kinds.PERSONAL: {
        "slug": "personal",
        "name": "Personal",
        "kind": OrganizationPlan.Kinds.PERSONAL,
        "max_members": 1,
        "can_open_cases": True,
        "can_manage_properties": True,
        "can_share_cases": True,
        "can_receive_cases": False,
        "can_accept_case_requests": False,
        "can_manage_members": False,
        "can_manage_billing": False,
        "can_view_all_org_cases": True,
        "can_use_ai_diagnostics": True,
    },
    OrganizationPlan.Kinds.PROFESSIONAL: {
        "slug": "professional",
        "name": "Professional",
        "kind": OrganizationPlan.Kinds.PROFESSIONAL,
        "max_members": 1,
        "can_open_cases": False,
        "can_manage_properties": False,
        "can_share_cases": False,
        "can_receive_cases": True,
        "can_accept_case_requests": True,
        "can_manage_members": True,
        "can_manage_billing": True,
        "can_view_all_org_cases": True,
        "can_use_ai_diagnostics": True,
    },
}


def get_or_create_builtin_plan(kind: str) -> OrganizationPlan:
    defaults = BUILTIN_PLAN_DEFINITIONS[kind].copy()
    slug = defaults.pop("slug")
    plan, _created = OrganizationPlan.objects.get_or_create(slug=slug, defaults=defaults)
    return plan


def build_personal_organization_name(user) -> str:
    display_name = " ".join(part for part in (user.first_name, user.last_name) if part).strip()
    if display_name:
        return display_name
    return user.email or f"Utente {user.pk}"


@transaction.atomic
def get_or_create_personal_organization(user) -> Organization:
    plan = get_or_create_builtin_plan(OrganizationPlan.Kinds.PERSONAL)
    organization, _created = Organization.objects.get_or_create(
        personal_owner=user,
        defaults={
            "name": build_personal_organization_name(user),
            "kind": Organization.Kinds.PERSONAL,
            "plan": plan,
            "created_by_user": user,
        },
    )
    OrganizationMembership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={
            "role": OrganizationMembership.Roles.OWNER,
            "scope": OrganizationMembership.Scopes.ORGANIZATION,
            "status": OrganizationMembership.Statuses.ACTIVE,
            "approved_by_user": user,
            "approved_at": timezone.now(),
        },
    )
    return organization


def user_has_active_organization_membership(user, organization_id: int | None) -> bool:
    if user.is_anonymous or organization_id is None:
        return False
    if getattr(user, "role", None) == "admin":
        return True
    return OrganizationMembership.objects.filter(
        user=user,
        organization_id=organization_id,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exists()


def normalize_invitation_email(email: str) -> str:
    from django.contrib.auth import get_user_model

    return get_user_model().objects.normalize_email(email)


def build_invitation_expiry():
    return timezone.now() + timedelta(days=settings.ORGANIZATION_INVITATION_TTL_DAYS)


def count_active_members_and_pending_invitations(organization) -> int:
    active_members = OrganizationMembership.objects.filter(
        organization=organization,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).count()
    pending_invitations = OrganizationInvitation.objects.filter(
        organization=organization,
        status=OrganizationInvitation.Statuses.PENDING,
        expires_at__gt=timezone.now(),
    ).count()
    return active_members + pending_invitations


def expire_invitation_if_needed(invitation) -> bool:
    if invitation.status == OrganizationInvitation.Statuses.PENDING and invitation.expires_at <= timezone.now():
        invitation.status = OrganizationInvitation.Statuses.EXPIRED
        invitation.save(update_fields=["status", "updated_at"])
        return True
    return False


def resolve_organization_invitation_token(token: str) -> OrganizationInvitation:
    try:
        payload = validate_organization_invitation_token(token)
    except signing.BadSignature as exc:
        raise ValidationError({"token": "Invalid invitation token."}) from exc

    invitation = (
        OrganizationInvitation.objects.select_related("organization", "organization__plan", "invited_by_user")
        .filter(id=payload.get("invitation_id"), email=payload.get("email"))
        .first()
    )
    if invitation is None:
        raise ValidationError({"token": "Invalid invitation token."})
    expire_invitation_if_needed(invitation)
    return invitation


def validate_organization_invitation_for_email(invitation, email: str) -> None:
    if invitation.status == OrganizationInvitation.Statuses.EXPIRED:
        raise ValidationError({"token": "Invitation expired."})
    if invitation.status != OrganizationInvitation.Statuses.PENDING:
        raise ValidationError({"token": "Invitation is not pending."})
    if email.lower() != invitation.email.lower():
        raise ValidationError({"token": "Invitation email does not match current user."})


def validate_organization_invitation_for_user(invitation, user) -> None:
    validate_organization_invitation_for_email(invitation, user.email)
    if OrganizationMembership.objects.filter(user=user, organization=invitation.organization).exists():
        raise ValidationError({"token": "Current user is already a member of the organization."})

    active_members = OrganizationMembership.objects.filter(
        organization=invitation.organization,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).count()
    if active_members >= invitation.organization.plan.max_members:
        raise ValidationError({"organization": "Organization member limit reached."})

    has_other_operational_membership = OrganizationMembership.objects.filter(
        user=user,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exclude(
        organization__kind=Organization.Kinds.PERSONAL,
    ).exclude(
        organization=invitation.organization,
    ).exists()
    if has_other_operational_membership and invitation.invited_by_user and invitation.invited_by_user.role != "admin":
        raise ValidationError({"token": "Multi-organization operational memberships require platform approval."})


@transaction.atomic
def accept_organization_invitation_for_user(invitation, user) -> tuple[OrganizationInvitation, OrganizationMembership]:
    try:
        locked_invitation = (
            OrganizationInvitation.objects.select_for_update()
            .select_related("organization", "organization__plan")
            .get(id=invitation.id)
        )
    except OrganizationInvitation.DoesNotExist as exc:
        raise ValidationError({"token": "Invalid invitation token."}) from exc
    expire_invitation_if_needed(locked_invitation)
    validate_organization_invitation_for_user(locked_invitation, user)

    membership = OrganizationMembership.objects.create(
        user=user,
        organization=locked_invitation.organization,
        role=locked_invitation.role,
        scope=locked_invitation.scope,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=locked_invitation.invited_by_user,
        approved_at=timezone.now(),
    )
    locked_invitation.status = OrganizationInvitation.Statuses.ACCEPTED
    locked_invitation.accepted_by_user = user
    locked_invitation.accepted_membership = membership
    locked_invitation.accepted_at = timezone.now()
    locked_invitation.save(
        update_fields=[
            "status",
            "accepted_by_user",
            "accepted_membership",
            "accepted_at",
            "updated_at",
        ]
    )
    return locked_invitation, membership
