import json
from datetime import timedelta

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.ai_assistant.models import AiDiagnosticSnapshot, AiSession, AiUsageLedger
from apps.cases.models import Case
from apps.guests.models import GuestSession
from apps.organizations.models import Organization
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticAdviceStep, DiagnosticChapter, DiagnosticChapterOption


def create_guest_session(client):
    response = client.post(reverse("api_v1:guests:guest-session-create"))
    assert response.status_code == 201
    return response.json()


def auth_headers(token):
    return {"HTTP_X_GUEST_TOKEN": token}


@pytest.mark.django_db
def test_guest_session_creation_returns_token_without_storing_plaintext(client):
    payload = create_guest_session(client)

    assert payload["guest_token"]
    assert payload["guest_session_id"]
    assert payload["quotas"]["ai_turn_limit"] == 2
    assert payload["quotas"]["ai_turns_remaining"] == 2

    session = GuestSession.objects.get(public_id=payload["guest_session_id"])
    assert session.status == GuestSession.Statuses.ACTIVE
    assert session.token_hash != payload["guest_token"]
    assert len(session.token_hash) == 64


@pytest.mark.django_db
def test_guest_current_requires_valid_token(client):
    response = client.get(reverse("api_v1:guests:guest-session-current"))
    assert response.status_code == 403

    payload = create_guest_session(client)
    current_response = client.get(
        reverse("api_v1:guests:guest-session-current"),
        **auth_headers(payload["guest_token"]),
    )
    assert current_response.status_code == 200
    assert current_response.json()["guest_session_id"] == payload["guest_session_id"]
    assert "guest_token" not in current_response.json()


@pytest.mark.django_db
def test_expired_guest_session_is_rejected(client):
    payload = create_guest_session(client)
    session = GuestSession.objects.get(public_id=payload["guest_session_id"])
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save(update_fields=["expires_at", "updated_at"])

    response = client.get(
        reverse("api_v1:guests:guest-session-current"),
        **auth_headers(payload["guest_token"]),
    )

    assert response.status_code == 403
    session.refresh_from_db()
    assert session.status == GuestSession.Statuses.EXPIRED


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_guest_diagnostic_turn_returns_advice_ai_snapshot_and_does_not_create_persistent_case(client):
    category = Category.objects.create(name="Elettricita", slug="guest-elettricita")
    chapter = DiagnosticChapter.objects.create(
        name="Problemi elettrici",
        slug="guest-problemi-elettrici",
        category=category,
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
    )
    option = DiagnosticChapterOption.objects.create(
        chapter=chapter,
        label="Quadro elettrico",
        slug="guest-quadro-elettrico",
        option_type=DiagnosticChapterOption.OptionTypes.ASSET_TYPE,
    )
    advice = DiagnosticAdviceStep.objects.create(
        chapter=chapter,
        chapter_option=option,
        title="Verifica esterna",
        slug="guest-verifica-esterna",
        body="Osserva solo elementi esterni e non aprire il quadro.",
    )
    guest_payload = create_guest_session(client)

    response = client.post(
        reverse("api_v1:guests:guest-diagnostic-turns"),
        data=json.dumps(
            {
                "diagnostic_chapter_id": chapter.id,
                "diagnostic_chapter_option_id": option.id,
                "message": "Sento odore di bruciato vicino al quadro elettrico",
                "use_ai": True,
            }
        ),
        content_type="application/json",
        **auth_headers(guest_payload["guest_token"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["advice_steps"][0]["id"] == advice.id
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["status"] == "completed"
    assert payload["diagnostic_snapshot"]["risk_level"] == "urgent"
    assert payload["diagnostic_snapshot"]["diagnostic_chapter_id"] == chapter.id
    assert payload["quotas"]["ai_turns_used"] == 1
    assert payload["call_to_action"] == {}

    message_response = client.get(
        reverse("api_v1:guests:guest-message-detail", args=[payload["assistant_message"]["id"]]),
        **auth_headers(guest_payload["guest_token"]),
    )
    assert message_response.status_code == 200
    assert message_response.json()["status"] == "completed"

    snapshot_response = client.get(
        reverse("api_v1:guests:guest-diagnostic-snapshot"),
        **auth_headers(guest_payload["guest_token"]),
    )
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["risk_level"] == "urgent"

    guest_session = GuestSession.objects.get(public_id=guest_payload["guest_session_id"])
    ai_session = AiSession.objects.get(guest_session=guest_session)
    assert ai_session.user_id is None
    assert ai_session.case_id is None
    assert AiDiagnosticSnapshot.objects.get(session=ai_session).risk_level == "urgent"
    usage = AiUsageLedger.objects.get(session=ai_session)
    assert usage.guest_session_id == guest_session.id
    assert usage.user_id is None
    assert usage.case_id is None
    assert Case.objects.count() == 0
    assert Organization.objects.count() == 0


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER="local",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    GUEST_AI_TURN_LIMIT=1,
)
def test_guest_ai_turn_limit_blocks_extra_ai_and_returns_call_to_action(client):
    category = Category.objects.create(name="Elettricita", slug="guest-limite-elettricita")
    chapter = DiagnosticChapter.objects.create(
        name="Problemi elettrici",
        slug="guest-limite-problemi-elettrici",
        category=category,
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
    )
    guest_payload = create_guest_session(client)

    for message in ["Il salvavita scatta", "Succede ancora"]:
        response = client.post(
            reverse("api_v1:guests:guest-diagnostic-turns"),
            data=json.dumps(
                {
                    "diagnostic_chapter_id": chapter.id,
                    "message": message,
                    "use_ai": True,
                }
            ),
            content_type="application/json",
            **auth_headers(guest_payload["guest_token"]),
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_message"] is None
    assert payload["assistant_message"] is None
    assert payload["quotas"]["ai_turns_used"] == 1
    assert payload["call_to_action"]["code"] == "guest_ai_limit_reached"

    guest_session = GuestSession.objects.get(public_id=guest_payload["guest_session_id"])
    ai_session = AiSession.objects.get(guest_session=guest_session)
    assert ai_session.messages.filter(role="user").count() == 1
