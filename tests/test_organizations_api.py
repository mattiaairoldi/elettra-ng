import json
from datetime import timedelta

import pytest
from django.core import mail
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationInvitation, OrganizationMembership, OrganizationPlan
from apps.organizations.services import get_or_create_personal_organization
from apps.organizations.tokens import generate_organization_invitation_token

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


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_organization_invitation_dispatches_email_through_celery_task(client, monkeypatch):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    invited_user = User.objects.create_user(email="tech@example.com", password="Password123!")
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
    get_or_create_personal_organization(invited_user)
    call_log = []

    from apps.organizations import views

    def tracked_delay(invitation_id):
        call_log.append(invitation_id)

    monkeypatch.setattr(views.send_organization_invitation_email_task, "delay", tracked_delay)

    client.force_login(owner)
    response = client.post(
        reverse("api_v1:organizations:organization-invitations", args=[organization.id]),
        data=json.dumps(
            {
                "email": invited_user.email,
                "role": OrganizationMembership.Roles.TECHNICIAN,
                "scope": OrganizationMembership.Scopes.ASSIGNED,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    invitation = OrganizationInvitation.objects.get(id=response.json()["id"])
    assert call_log == [invitation.id]
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_organization_invitation_email_is_sent_by_celery_task(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    invited_user = User.objects.create_user(email="tech@example.com", password="Password123!")
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

    client.force_login(owner)
    response = client.post(
        reverse("api_v1:organizations:organization-invitations", args=[organization.id]),
        data=json.dumps(
            {
                "email": invited_user.email,
                "role": OrganizationMembership.Roles.TECHNICIAN,
                "scope": OrganizationMembership.Scopes.ASSIGNED,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [invited_user.email]
    assert "invitation" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_organization_invitation_email_task_ignores_non_pending_invitation():
    from apps.organizations.tasks import send_organization_invitation_email_task

    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    plan = OrganizationPlan.objects.get(slug="professional")
    organization = Organization.objects.create(
        name="Rossi Impianti",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=owner,
    )
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email="tech@example.com",
        role=OrganizationMembership.Roles.TECHNICIAN,
        scope=OrganizationMembership.Scopes.ASSIGNED,
        status=OrganizationInvitation.Statuses.REVOKED,
        invited_by_user=owner,
        revoked_by_user=owner,
        revoked_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
    )

    send_organization_invitation_email_task(invitation.id)

    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_accept_organization_invitation_creates_membership(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    invited_user = User.objects.create_user(email="tech@example.com", password="Password123!")
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
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=invited_user.email,
        role=OrganizationMembership.Roles.TECHNICIAN,
        scope=OrganizationMembership.Scopes.ASSIGNED,
        invited_by_user=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )
    token = generate_organization_invitation_token(invitation)

    client.force_login(invited_user)
    response = client.post(
        reverse("api_v1:organizations:organization-invitation-accept"),
        data=json.dumps({"token": token}),
        content_type="application/json",
    )

    assert response.status_code == 200
    invitation.refresh_from_db()
    assert invitation.status == OrganizationInvitation.Statuses.ACCEPTED
    assert invitation.accepted_by_user == invited_user
    assert OrganizationMembership.objects.filter(
        user=invited_user,
        organization=organization,
        role=OrganizationMembership.Roles.TECHNICIAN,
        scope=OrganizationMembership.Scopes.ASSIGNED,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exists()


@pytest.mark.django_db
def test_revoked_organization_invitation_cannot_be_accepted(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    invited_user = User.objects.create_user(email="tech@example.com", password="Password123!")
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
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=invited_user.email,
        role=OrganizationMembership.Roles.TECHNICIAN,
        scope=OrganizationMembership.Scopes.ASSIGNED,
        status=OrganizationInvitation.Statuses.REVOKED,
        invited_by_user=owner,
        revoked_by_user=owner,
        revoked_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=7),
    )
    token = generate_organization_invitation_token(invitation)

    client.force_login(invited_user)
    response = client.post(
        reverse("api_v1:organizations:organization-invitation-accept"),
        data=json.dumps({"token": token}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"token": ["Invitation is not pending."]}
