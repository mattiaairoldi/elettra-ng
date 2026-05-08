from django.db import transaction
from django.utils import timezone

from .models import Organization, OrganizationMembership, OrganizationPlan


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

