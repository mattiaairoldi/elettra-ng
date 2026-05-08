import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.organizations.models import Organization, OrganizationMembership, OrganizationPlan
from apps.organizations.services import get_or_create_personal_organization

User = get_user_model()


@pytest.mark.django_db
def test_user_can_create_professional_organization(client):
    user = User.objects.create_user(email="owner@example.com", password="Password123!")
    client.force_login(user)

    response = client.post(
        reverse("api_v1:organizations:organization-list"),
        data=json.dumps({"name": "Rossi Impianti"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Rossi Impianti"
    assert body["kind"] == Organization.Kinds.PROFESSIONAL
    assert body["plan"]["slug"] == "professional"

    organization = Organization.objects.get(id=body["id"])
    assert OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exists()


@pytest.mark.django_db
def test_organization_membership_create_for_existing_user(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    technician = User.objects.create_user(email="tech@example.com", password="Password123!")
    plan = OrganizationPlan.objects.get(slug="professional")
    plan.max_members = 2
    plan.save(update_fields=["max_members", "updated_at"])
    organization = Organization.objects.create(
        name="Rossi Impianti",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=owner,
    )
    OrganizationMembership.objects.create(
        user=owner,
        organization=organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=owner,
    )
    get_or_create_personal_organization(technician)

    client.force_login(owner)
    response = client.post(
        reverse("api_v1:organizations:organization-memberships", args=[organization.id]),
        data=json.dumps(
            {
                "email": technician.email,
                "role": OrganizationMembership.Roles.TECHNICIAN,
                "scope": OrganizationMembership.Scopes.ASSIGNED,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_email"] == technician.email
    assert body["role"] == OrganizationMembership.Roles.TECHNICIAN
    assert body["scope"] == OrganizationMembership.Scopes.ASSIGNED
    assert body["status"] == OrganizationMembership.Statuses.ACTIVE


@pytest.mark.django_db
def test_organization_membership_create_enforces_plan_member_limit(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    technician = User.objects.create_user(email="tech@example.com", password="Password123!")
    plan = OrganizationPlan.objects.get(slug="professional")
    organization = Organization.objects.create(
        name="Rossi Impianti",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=owner,
    )
    OrganizationMembership.objects.create(
        user=owner,
        organization=organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=owner,
    )

    client.force_login(owner)
    response = client.post(
        reverse("api_v1:organizations:organization-memberships", args=[organization.id]),
        data=json.dumps(
            {
                "email": technician.email,
                "role": OrganizationMembership.Roles.TECHNICIAN,
                "scope": OrganizationMembership.Scopes.ASSIGNED,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"organization": ["Organization member limit reached."]}


@pytest.mark.django_db
def test_non_manager_cannot_create_organization_membership(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    technician = User.objects.create_user(email="tech@example.com", password="Password123!")
    new_user = User.objects.create_user(email="new@example.com", password="Password123!")
    plan = OrganizationPlan.objects.get(slug="professional")
    plan.max_members = 3
    plan.save(update_fields=["max_members", "updated_at"])
    organization = Organization.objects.create(
        name="Rossi Impianti",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=owner,
    )
    OrganizationMembership.objects.create(
        user=owner,
        organization=organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=owner,
    )
    OrganizationMembership.objects.create(
        user=technician,
        organization=organization,
        role=OrganizationMembership.Roles.TECHNICIAN,
        scope=OrganizationMembership.Scopes.ASSIGNED,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=owner,
    )

    client.force_login(technician)
    response = client.post(
        reverse("api_v1:organizations:organization-memberships", args=[organization.id]),
        data=json.dumps(
            {
                "email": new_user.email,
                "role": OrganizationMembership.Roles.TECHNICIAN,
                "scope": OrganizationMembership.Scopes.ASSIGNED,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"organization": ["You cannot manage this organization."]}


@pytest.mark.django_db
def test_operational_multi_organization_membership_requires_platform_admin(client):
    first_owner = User.objects.create_user(email="first-owner@example.com", password="Password123!")
    second_owner = User.objects.create_user(email="second-owner@example.com", password="Password123!")
    technician = User.objects.create_user(email="tech@example.com", password="Password123!")
    plan = OrganizationPlan.objects.get(slug="professional")
    plan.max_members = 2
    plan.save(update_fields=["max_members", "updated_at"])
    first_organization = Organization.objects.create(
        name="Primo Studio",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=first_owner,
    )
    second_organization = Organization.objects.create(
        name="Secondo Studio",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=second_owner,
    )
    OrganizationMembership.objects.create(
        user=technician,
        organization=first_organization,
        role=OrganizationMembership.Roles.TECHNICIAN,
        scope=OrganizationMembership.Scopes.ASSIGNED,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=first_owner,
    )
    OrganizationMembership.objects.create(
        user=second_owner,
        organization=second_organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=second_owner,
    )

    client.force_login(second_owner)
    response = client.post(
        reverse("api_v1:organizations:organization-memberships", args=[second_organization.id]),
        data=json.dumps(
            {
                "email": technician.email,
                "role": OrganizationMembership.Roles.TECHNICIAN,
                "scope": OrganizationMembership.Scopes.ASSIGNED,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"email": ["Multi-organization operational memberships require platform approval."]}

