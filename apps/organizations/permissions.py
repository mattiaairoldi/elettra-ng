from .models import OrganizationMembership


MANAGER_ROLES = {
    OrganizationMembership.Roles.OWNER,
    OrganizationMembership.Roles.ADMIN,
}


def user_can_manage_organization(user, organization) -> bool:
    if user.role == "admin":
        return True
    if not organization.plan.can_manage_members:
        return False
    return OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Statuses.ACTIVE,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        role__in=MANAGER_ROLES,
    ).exists()


def user_can_view_organization(user, organization) -> bool:
    if user.role == "admin":
        return True
    return OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exists()

