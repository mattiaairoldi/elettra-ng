import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cases.models import Case, CaseShareRequest
from apps.conversations.models import Conversation, ConversationPost
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
def test_case_share_request_acceptance_opens_conversation(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    case = Case.objects.create(
        customer_user=customer,
        category=category,
        title="Salvavita abbassato",
        description="Scatta quando accendo il forno.",
    )

    client.force_login(customer)
    share_response = client.post(
        reverse("api_v1:cases:case-share-requests", args=[case.id]),
        data=json.dumps(
            {
                "recipient_organization_id": professional_organization.id,
                "share_scope": CaseShareRequest.ShareScopes.SUMMARY,
                "visible_summary": "Il salvavita scatta con il forno.",
            }
        ),
        content_type="application/json",
    )
    assert share_response.status_code == 201
    share_request_id = share_response.json()["id"]

    client.force_login(professional)
    accept_response = client.post(
        reverse("api_v1:cases:case-share-request-accept", args=[share_request_id]),
        content_type="application/json",
    )
    assert accept_response.status_code == 200
    conversation_id = accept_response.json()["conversation_id"]

    share_request = CaseShareRequest.objects.get(id=share_request_id)
    assert share_request.status == CaseShareRequest.Statuses.ACCEPTED
    assert share_request.conversation.id == conversation_id
    assert Conversation.objects.filter(id=conversation_id, case=case).exists()

    case.refresh_from_db()
    assert case.status == Case.Statuses.WAITING_PROFESSIONAL

    detail_response = client.get(reverse("api_v1:cases:case-detail", args=[case.id]))
    assert detail_response.status_code == 200


@pytest.mark.django_db
def test_case_share_requests_can_be_listed_by_recipient_status(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    CaseShareRequest.objects.create(
        case=case,
        requester_user=customer,
        recipient_organization=professional_organization,
        status=CaseShareRequest.Statuses.PENDING,
        visible_title=case.title,
    )

    client.force_login(professional)
    response = client.get(
        reverse("api_v1:cases:case-share-request-list"),
        {"status": CaseShareRequest.Statuses.PENDING},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["visible_title"] == "Salvavita abbassato"


@pytest.mark.django_db
def test_conversation_posts_remain_visible_after_case_share_revocation(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Idraulica", slug="idraulica")
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
    post_response = client.post(
        reverse("api_v1:conversations:conversation-posts", args=[conversation_id]),
        data=json.dumps({"body": "Posso passare domani per una verifica."}),
        content_type="application/json",
    )
    assert post_response.status_code == 201
    assert ConversationPost.objects.filter(conversation_id=conversation_id).count() == 1

    client.force_login(customer)
    revoke_response = client.post(reverse("api_v1:cases:case-share-request-revoke", args=[share_request_id]))
    assert revoke_response.status_code == 200

    client.force_login(professional)
    case_response = client.get(reverse("api_v1:cases:case-detail", args=[case.id]))
    assert case_response.status_code == 404

    posts_response = client.get(reverse("api_v1:conversations:conversation-posts", args=[conversation_id]))
    assert posts_response.status_code == 200
    assert posts_response.json()[0]["body"] == "Posso passare domani per una verifica."


@pytest.mark.django_db
def test_case_share_request_can_be_rejected_with_optional_reason(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_organization, _membership = create_professional_organization(professional)
    category = Category.objects.create(name="Domotica", slug="domotica")
    case = Case.objects.create(customer_user=customer, category=category, title="Hub offline")

    client.force_login(customer)
    share_response = client.post(
        reverse("api_v1:cases:case-share-requests", args=[case.id]),
        data=json.dumps({"recipient_organization_id": professional_organization.id}),
        content_type="application/json",
    )
    share_request_id = share_response.json()["id"]

    client.force_login(professional)
    reject_response = client.post(
        reverse("api_v1:cases:case-share-request-reject", args=[share_request_id]),
        data=json.dumps({"reason": "Non ho disponibilita questa settimana."}),
        content_type="application/json",
    )
    assert reject_response.status_code == 200

    share_request = CaseShareRequest.objects.get(id=share_request_id)
    assert share_request.status == CaseShareRequest.Statuses.REJECTED
    assert share_request.rejection_reason == "Non ho disponibilita questa settimana."
