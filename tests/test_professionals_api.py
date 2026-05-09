import pytest
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.professionals.models import ProfessionalProfile
from apps.organizations.models import Organization, OrganizationMembership, OrganizationPlan
from apps.taxonomy.models import Category, Tag

User = get_user_model()


@pytest.mark.django_db
def test_professionals_list_returns_only_available_professionals(client):
    user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    available = ProfessionalProfile.objects.create(user=user, display_name="Mario Rossi", is_available=True)

    other_user = User.objects.create_user(
        email="pro2@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    ProfessionalProfile.objects.create(user=other_user, display_name="Luigi Bianchi", is_available=False)

    response = client.get(reverse("api_v1:professionals:professional-list"))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [available.id]


@pytest.mark.django_db
def test_professionals_list_supports_category_tag_and_search_filters(client):
    user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    category = Category.objects.create(name="Idraulica", slug="idraulica")
    tag = Tag.objects.create(name="Perdite", slug="perdite", category=category)
    profile = ProfessionalProfile.objects.create(
        user=user,
        display_name="Idraulico Milano",
        service_area_text="Milano e provincia",
    )
    profile.categories.add(category)
    profile.tags.add(tag)

    category_response = client.get(
        reverse("api_v1:professionals:professional-list"),
        {"category_id": category.id},
    )
    assert category_response.status_code == 200
    assert [item["id"] for item in category_response.json()] == [profile.id]

    tag_response = client.get(reverse("api_v1:professionals:professional-list"), {"tag_id": tag.id})
    assert tag_response.status_code == 200
    assert [item["id"] for item in tag_response.json()] == [profile.id]

    search_response = client.get(reverse("api_v1:professionals:professional-list"), {"q": "milano"})
    assert search_response.status_code == 200
    assert [item["id"] for item in search_response.json()] == [profile.id]


@pytest.mark.django_db
def test_professional_detail_returns_available_profile(client):
    user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    profile = ProfessionalProfile.objects.create(user=user, display_name="Tecnico Casa")

    response = client.get(reverse("api_v1:professionals:professional-detail", args=[profile.id]))

    assert response.status_code == 200
    assert response.json()["display_name"] == "Tecnico Casa"


@pytest.mark.django_db
def test_professional_profile_exposes_case_share_recipient_ids_when_available(client):
    user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    plan = OrganizationPlan.objects.create(
        slug="professional-demo",
        name="Professional demo",
        kind=OrganizationPlan.Kinds.PROFESSIONAL,
        can_receive_cases=True,
    )
    organization = Organization.objects.create(
        name="Tecnici Demo",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
    )
    membership = OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
    )
    profile = ProfessionalProfile.objects.create(user=user, display_name="Tecnico Casa")

    response = client.get(reverse("api_v1:professionals:professional-detail", args=[profile.id]))

    assert response.status_code == 200
    assert response.json()["recipient_organization_id"] == organization.id
    assert response.json()["recipient_membership_id"] == membership.id


@pytest.mark.django_db
def test_professionals_list_orders_by_distance_when_coordinates_are_provided(client):
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    near_user = User.objects.create_user(
        email="near@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    far_user = User.objects.create_user(
        email="far@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    near = ProfessionalProfile.objects.create(
        user=near_user,
        display_name="Tecnico vicino",
        location=Point(9.19, 45.4642, srid=4326),
    )
    far = ProfessionalProfile.objects.create(
        user=far_user,
        display_name="Tecnico lontano",
        location=Point(12.4964, 41.9028, srid=4326),
    )
    near.categories.add(category)
    far.categories.add(category)

    response = client.get(
        reverse("api_v1:professionals:professional-list"),
        {"category_id": category.id, "latitude": 45.4642, "longitude": 9.19},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [near.id, far.id]
    assert body[0]["distance_km"] == 0.0
    assert body[0]["location"] == {"latitude": 45.4642, "longitude": 9.19}
