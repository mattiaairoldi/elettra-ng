import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cases.models import Case, Property
from apps.organizations.models import OrganizationMembership, OrganizationPlan
from apps.taxonomy.models import Category
from apps.identity.serializers import RegisterSerializer

User = get_user_model()


@pytest.mark.django_db
def test_property_creates_personal_organization_membership():
    user = User.objects.create_user(email="customer@example.com", password="Password123!")

    property_obj = Property.objects.create(owner_user=user, name="Casa")

    property_obj.refresh_from_db()
    assert property_obj.organization.kind == "personal"
    assert property_obj.organization.plan.slug == "personal"
    assert property_obj.organization.personal_owner == user
    assert OrganizationMembership.objects.filter(
        user=user,
        organization=property_obj.organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exists()


@pytest.mark.django_db
def test_case_uses_property_organization_when_property_is_selected():
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    property_obj = Property.objects.create(owner_user=user, name="Casa")

    case = Case.objects.create(customer_user=user, category=category, property=property_obj, title="Guasto")

    assert case.owner_organization == property_obj.organization


@pytest.mark.django_db
def test_case_without_property_uses_requester_personal_organization():
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita")

    case = Case.objects.create(customer_user=user, category=category, title="Guasto")

    assert case.owner_organization.kind == "personal"
    assert case.owner_organization.personal_owner == user


@pytest.mark.django_db
def test_builtin_organization_plans_are_seeded():
    assert OrganizationPlan.objects.filter(slug="personal", can_open_cases=True, max_members=1).exists()
    assert OrganizationPlan.objects.filter(slug="professional", can_receive_cases=True, max_members=1).exists()


@pytest.mark.django_db
def test_registration_creates_personal_organization():
    serializer = RegisterSerializer(
        data={
            "email": "customer@example.com",
            "password": "Password123!",
            "first_name": "Mario",
            "last_name": "Rossi",
        }
    )
    assert serializer.is_valid(), serializer.errors

    user = serializer.save()

    assert user.personal_organization.kind == "personal"
    assert user.personal_organization.name == "Mario Rossi"


@pytest.mark.django_db
def test_property_and_case_api_expose_organization_ids(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(user)
    category = Category.objects.create(name="Elettricita", slug="elettricita")

    property_response = client.post(
        reverse("api_v1:cases:property-list"),
        data=json.dumps({"name": "Casa"}),
        content_type="application/json",
    )
    assert property_response.status_code == 201
    property_id = property_response.json()["id"]
    organization_id = property_response.json()["organization_id"]

    case_response = client.post(
        reverse("api_v1:cases:case-list"),
        data=json.dumps(
            {
                "category_id": category.id,
                "property_id": property_id,
                "title": "Salvavita abbassato",
            }
        ),
        content_type="application/json",
    )
    assert case_response.status_code == 201
    assert case_response.json()["owner_organization_id"] == organization_id
