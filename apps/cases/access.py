from django.db.models import Q

from apps.organizations.models import OrganizationMembership


def build_case_visibility_filter(user):
    if user.role == "admin":
        return Q()
    active_membership = Q(
        owner_organization__memberships__user=user,
        owner_organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
    )
    accepted_direct_share = Q(
        share_requests__status="accepted",
        share_requests__recipient_membership__user=user,
        share_requests__recipient_membership__status=OrganizationMembership.Statuses.ACTIVE,
    )
    accepted_org_share = Q(
        share_requests__status="accepted",
        share_requests__recipient_membership__isnull=True,
        share_requests__recipient_organization__memberships__user=user,
        share_requests__recipient_organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
        share_requests__recipient_organization__memberships__scope=OrganizationMembership.Scopes.ORGANIZATION,
    )
    return Q(customer_user=user) | Q(assigned_professional=user) | active_membership | accepted_direct_share | accepted_org_share


def user_can_access_case(user, case) -> bool:
    if user.role == "admin":
        return True
    from .models import Case

    return Case.objects.filter(pk=case.pk).filter(build_case_visibility_filter(user)).exists()


def user_can_share_case(user, case) -> bool:
    if user.role == "admin":
        return True
    return OrganizationMembership.objects.filter(
        user=user,
        organization=case.owner_organization,
        status=OrganizationMembership.Statuses.ACTIVE,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
    ).exists()


def get_active_membership(user, organization):
    return (
        OrganizationMembership.objects.filter(
            user=user,
            organization=organization,
            status=OrganizationMembership.Statuses.ACTIVE,
        )
        .order_by("id")
        .first()
    )


def user_can_respond_to_share_request(user, share_request) -> bool:
    if user.role == "admin":
        return True

    if (
        share_request.recipient_membership_id
        and share_request.recipient_membership.user_id == user.id
        and share_request.recipient_membership.status == OrganizationMembership.Statuses.ACTIVE
    ):
        return True

    return OrganizationMembership.objects.filter(
        user=user,
        organization=share_request.recipient_organization,
        status=OrganizationMembership.Statuses.ACTIVE,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        role__in={
            OrganizationMembership.Roles.OWNER,
            OrganizationMembership.Roles.ADMIN,
            OrganizationMembership.Roles.ADMINISTRATIVE,
        },
    ).exists()

