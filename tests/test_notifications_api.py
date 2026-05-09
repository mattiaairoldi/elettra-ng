import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cases.models import Case, CaseShareRequest
from apps.conversations.models import Conversation, ConversationPost
from apps.notifications.models import DeviceInstallation, Notification
from apps.notifications.services import create_notification
from apps.organizations.models import Organization, OrganizationMembership, OrganizationPlan
from apps.taxonomy.models import Category

User = get_user_model()


def create_professional_organization(user):
    plan = OrganizationPlan.objects.get(slug="professional")
    organization = Organization.objects.create(
        name="Tecnici Rossi",
        kind=Organization.Kinds.PROFESSIONAL,
        plan=plan,
        created_by_user=user,
    )
    membership = OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=OrganizationMembership.Roles.OWNER,
        scope=OrganizationMembership.Scopes.ORGANIZATION,
        status=OrganizationMembership.Statuses.ACTIVE,
        approved_by_user=user,
    )
    return organization, membership


@pytest.mark.django_db
def test_notification_list_summary_and_mark_read(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    other_user = User.objects.create_user(email="other@example.com", password="Password123!")
    notification = create_notification(
        recipient_user=user,
        actor_user=other_user,
        notification_type=Notification.Types.SYSTEM,
        title="Promemoria",
        body="Controlla una scadenza.",
        target_type="asset_maintenance_reminder",
        target_id=42,
    )
    create_notification(
        recipient_user=other_user,
        notification_type=Notification.Types.SYSTEM,
        title="Notifica altra persona",
    )
    client.force_login(user)

    list_response = client.get(reverse("api_v1:notifications:notification-list"))
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [notification.id]
    assert list_response.json()[0]["is_read"] is False

    summary_response = client.get(reverse("api_v1:notifications:notification-summary"))
    assert summary_response.status_code == 200
    assert summary_response.json() == {"unread_count": 1}

    read_response = client.post(reverse("api_v1:notifications:notification-read", args=[notification.id]))
    assert read_response.status_code == 200
    assert read_response.json()["notification"]["is_read"] is True

    unread_response = client.get(reverse("api_v1:notifications:notification-list"), {"unread": "true"})
    assert unread_response.status_code == 200
    assert unread_response.json() == []


@pytest.mark.django_db
def test_mark_all_read_updates_only_current_user(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    other_user = User.objects.create_user(email="other@example.com", password="Password123!")
    create_notification(recipient_user=user, notification_type=Notification.Types.SYSTEM, title="Prima")
    create_notification(recipient_user=user, notification_type=Notification.Types.SYSTEM, title="Seconda")
    create_notification(recipient_user=other_user, notification_type=Notification.Types.SYSTEM, title="Altra")
    client.force_login(user)

    response = client.post(reverse("api_v1:notifications:notification-mark-all-read"))
    assert response.status_code == 200
    assert response.json() == {"updated_count": 2}
    assert Notification.objects.filter(recipient_user=user, read_at__isnull=True).count() == 0
    assert Notification.objects.filter(recipient_user=other_user, read_at__isnull=True).count() == 1


@pytest.mark.django_db
def test_device_installation_register_update_and_soft_delete(client):
    user = User.objects.create_user(email="mobile@example.com", password="Password123!")
    client.force_login(user)

    create_response = client.post(
        reverse("api_v1:notifications:device-installation-list"),
        data=json.dumps(
            {
                "platform": DeviceInstallation.Platforms.IOS,
                "push_provider": DeviceInstallation.PushProviders.FCM,
                "push_token": "provider-token-1",
                "app_version": "1.0.0",
                "device_model": "iPhone",
                "locale": "it-IT",
                "timezone": "Europe/Rome",
            }
        ),
        content_type="application/json",
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert "push_token" not in body
    assert body["user_id"] == user.id
    assert body["is_active"] is True
    installation_id = body["installation_id"]

    update_response = client.post(
        reverse("api_v1:notifications:device-installation-list"),
        data=json.dumps(
            {
                "installation_id": installation_id,
                "platform": DeviceInstallation.Platforms.IOS,
                "push_provider": DeviceInstallation.PushProviders.APNS,
                "push_token": "provider-token-2",
                "app_version": "1.1.0",
            }
        ),
        content_type="application/json",
    )
    assert update_response.status_code == 201
    assert DeviceInstallation.objects.filter(user=user).count() == 1
    installation = DeviceInstallation.objects.get(user=user)
    assert installation.push_provider == DeviceInstallation.PushProviders.APNS
    assert installation.push_token == "provider-token-2"
    assert installation.app_version == "1.1.0"

    delete_response = client.delete(reverse("api_v1:notifications:device-installation-detail", args=[installation.id]))
    assert delete_response.status_code == 204
    installation.refresh_from_db()
    assert installation.is_active is False
    assert installation.deactivated_at is not None


@pytest.mark.django_db
def test_device_installation_cannot_update_another_users_installation(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    other_user = User.objects.create_user(email="other@example.com", password="Password123!")
    installation = DeviceInstallation.objects.create(user=owner, platform=DeviceInstallation.Platforms.WEB)
    client.force_login(other_user)

    response = client.post(
        reverse("api_v1:notifications:device-installation-list"),
        data=json.dumps({"installation_id": str(installation.installation_id), "platform": "web"}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json() == {"installation_id": ["Installation belongs to another user."]}


@pytest.mark.django_db
def test_case_share_request_creates_in_app_notification_for_recipient(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Elettricita", slug="elettricita-notifications")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)

    response = client.post(
        reverse("api_v1:cases:case-share-requests", args=[case.id]),
        data=json.dumps({"recipient_organization_id": professional_organization.id}),
        content_type="application/json",
    )

    assert response.status_code == 201
    notification = Notification.objects.get(recipient_user=professional)
    assert notification.notification_type == Notification.Types.CASE_SHARE_REQUEST_CREATED
    assert notification.actor_user == customer
    assert notification.target_id == str(response.json()["id"])


@pytest.mark.django_db
def test_conversation_post_notifies_other_participants(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Idraulica", slug="idraulica-notifications")
    case = Case.objects.create(customer_user=customer, category=category, title="Perdita sotto lavello")

    client.force_login(customer)
    share_response = client.post(
        reverse("api_v1:cases:case-share-requests", args=[case.id]),
        data=json.dumps({"recipient_organization_id": professional_organization.id}),
        content_type="application/json",
    )
    share_request_id = share_response.json()["id"]

    client.force_login(professional)
    accept_response = client.post(reverse("api_v1:cases:case-share-request-accept", args=[share_request_id]))
    conversation_id = accept_response.json()["conversation_id"]
    Notification.objects.all().delete()

    post_response = client.post(
        reverse("api_v1:conversations:conversation-posts", args=[conversation_id]),
        data=json.dumps({"body": "Posso passare domani per una verifica."}),
        content_type="application/json",
    )

    assert post_response.status_code == 201
    post = ConversationPost.objects.get(id=post_response.json()["id"])
    assert Conversation.objects.filter(id=conversation_id, posts=post).exists()
    notification = Notification.objects.get(recipient_user=customer)
    assert notification.notification_type == Notification.Types.CONVERSATION_POST_CREATED
    assert notification.actor_user == professional
    assert notification.target_id == str(conversation_id)
    assert not Notification.objects.filter(recipient_user=professional).exists()


@pytest.mark.django_db
def test_case_share_revocation_notifies_recipient(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Clima", slug="clima-revocation-notifications")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima non raffredda")

    client.force_login(customer)
    share_response = client.post(
        reverse("api_v1:cases:case-share-requests", args=[case.id]),
        data=json.dumps({"recipient_organization_id": professional_organization.id}),
        content_type="application/json",
    )
    share_request_id = share_response.json()["id"]

    client.force_login(professional)
    accept_response = client.post(reverse("api_v1:cases:case-share-request-accept", args=[share_request_id]))
    assert accept_response.status_code == 200
    Notification.objects.all().delete()

    client.force_login(customer)
    revoke_response = client.post(reverse("api_v1:cases:case-share-request-revoke", args=[share_request_id]))

    assert revoke_response.status_code == 200
    notification = Notification.objects.get(recipient_user=professional)
    assert notification.notification_type == Notification.Types.CASE_SHARE_REQUEST_REVOKED
    assert notification.actor_user == customer
    assert notification.target_id == str(share_request_id)
