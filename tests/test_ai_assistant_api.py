import json
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from apps.cases.models import Case, CaseEvent
from apps.ai_assistant.models import AiDiagnosticSnapshot, AiMessage
from apps.ai_assistant.tasks import generate_ai_diagnostic_reply_task, generate_ai_reply_task
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticFlow, DiagnosticNode

User = get_user_model()


@pytest.mark.django_db
def test_customer_can_create_and_reuse_ai_session_for_own_case(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)

    first_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    assert first_response.status_code == 201

    second_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]


@pytest.mark.django_db
def test_customer_cannot_create_ai_session_for_foreign_case(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    other_user = User.objects.create_user(email="other@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-ai")
    case = Case.objects.create(customer_user=owner, category=category, title="Clima non raffredda")
    client.force_login(other_user)

    response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json() == {"case_id": ["You do not own this case."]}


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_message_flow_returns_contextual_reply_and_history(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-flow")
    flow = DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-ai-flow",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    node = DiagnosticNode.objects.create(
        flow=flow,
        title="Il salvavita scatta subito?",
        node_type=DiagnosticNode.NodeTypes.QUESTION,
        is_entrypoint=True,
    )
    case = Case.objects.create(
        customer_user=customer,
        category=category,
        title="Salvavita abbassato",
        status=Case.Statuses.IN_DIAGNOSIS,
        troubleshooting_flow=flow,
        current_diagnostic_node=node,
    )
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Ho gia' controllato il quadro, cosa verifico ora?"}),
        content_type="application/json",
    )
    assert message_response.status_code == 202
    assert message_response.json()["assistant_message"]["status"] == "completed"
    assert "Pratica" in message_response.json()["assistant_message"]["content"]
    assert "Nodo diagnostico corrente" in message_response.json()["assistant_message"]["content"]

    history_response = client.get(reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]))
    assert history_response.status_code == 200
    assert [item["role"] for item in history_response.json()] == ["user", "assistant"]
    assert [item["status"] for item in history_response.json()] == ["completed", "completed"]


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_diagnostic_turn_updates_snapshot_case_status_and_events(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-diagnostic")
    case = Case.objects.create(customer_user=customer, category=category, title="Odore dal quadro")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    turn_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-diagnostic-turns", args=[session_id]),
        data=json.dumps({"content": "Sento odore di bruciato vicino al quadro elettrico"}),
        content_type="application/json",
    )

    assert turn_response.status_code == 202
    payload = turn_response.json()
    assert payload["assistant_message"]["status"] == "completed"
    assert payload["assistant_message"]["metadata_json"]["diagnostic"]["risk_level"] == "urgent"
    assert payload["diagnostic_snapshot"]["risk_level"] == "urgent"
    assert payload["diagnostic_snapshot"]["escalation_recommended"] is True
    assert "professionista" in payload["assistant_message"]["content"]

    snapshot_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-diagnostic-snapshot", args=[session_id])
    )
    assert snapshot_response.status_code == 200
    assert snapshot_response.json()["id"] == payload["diagnostic_snapshot"]["id"]

    case.refresh_from_db()
    assert case.status == Case.Statuses.IN_DIAGNOSIS
    event = CaseEvent.objects.get(case=case, event_type=CaseEvent.EventTypes.AI_DIAGNOSTIC_PROGRESS)
    assert event.actor_user_id == customer.id
    assert event.payload_json["risk_level"] == "urgent"
    assert event.payload_json["escalation_recommended"] is True


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_diagnostic_turn_requires_linked_case(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    turn_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-diagnostic-turns", args=[session_id]),
        data=json.dumps({"content": "Vorrei iniziare una diagnosi"}),
        content_type="application/json",
    )

    assert turn_response.status_code == 400
    assert turn_response.json() == {"case": ["Diagnostic turns require a linked case."]}


@pytest.mark.django_db
@override_settings(AI_DAILY_MESSAGE_LIMIT_PER_USER=1, CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_daily_message_limit_is_enforced(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-limit")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    first_message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Primo messaggio"}),
        content_type="application/json",
    )
    assert first_message_response.status_code == 202

    second_message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Secondo messaggio"}),
        content_type="application/json",
    )
    assert second_message_response.status_code == 400
    assert second_message_response.json() == {"limit": ["Daily AI message limit reached."]}


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER="openai",
    OPENAI_API_KEY="test-key",
    AI_OPENAI_MODEL="gpt-5.4-mini",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_ai_message_flow_can_use_openai_provider(client, monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-ai-openai")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima non raffredda")
    client.force_login(customer)

    captured = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs
            self.responses = self

        def create(self, **kwargs):
            captured["request"] = kwargs
            if kwargs.get("stream") is True:
                return [
                    SimpleNamespace(type="response.output_text.delta", delta="Risposta "),
                    SimpleNamespace(type="response.output_text.delta", delta="OpenAI "),
                    SimpleNamespace(type="response.output_text.delta", delta="di test"),
                ]
            return SimpleNamespace(output_text="Risposta OpenAI di test")

    monkeypatch.setattr("apps.ai_assistant.provider.OpenAI", FakeClient, raising=False)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Il clima non raffredda piu' come prima"}),
        content_type="application/json",
    )

    assert message_response.status_code == 202
    assert message_response.json()["assistant_message"]["content"] == "Risposta OpenAI di test"
    assert message_response.json()["assistant_message"]["status"] == "completed"
    assert captured["client_kwargs"] == {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
    }
    assert captured["request"]["model"] == "gpt-5.4-mini"
    assert captured["request"]["store"] is False
    assert captured["request"]["stream"] is True
    assert captured["request"]["input"][-1] == {
        "role": "user",
        "content": "Il clima non raffredda piu' come prima",
    }


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER="openai",
    OPENAI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_ai_message_flow_marks_assistant_message_as_failed_when_openai_provider_is_not_configured(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-missing")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Cosa posso controllare?"}),
        content_type="application/json",
    )

    assert message_response.status_code == 202
    assert message_response.json()["assistant_message"]["status"] == "failed"
    assert message_response.json()["assistant_message"]["error_detail"] == "OPENAI_API_KEY is not configured."


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=False, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_message_flow_returns_queued_assistant_message_when_async_is_not_eager(client, monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-queued")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)
    dispatched = []

    from apps.ai_assistant import views

    def fake_delay(message_id):
        dispatched.append(message_id)

    monkeypatch.setattr(views.generate_ai_reply_task, "delay", fake_delay)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Messaggio async"}),
        content_type="application/json",
    )

    assert message_response.status_code == 202
    assert len(dispatched) == 1
    assert message_response.json()["assistant_message"]["status"] == "queued"
    assert message_response.json()["assistant_message"]["content"] == ""


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_polling_endpoints_support_incremental_fetch_and_status_snapshot(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-ai-polling")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima rumoroso")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    first_message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Primo messaggio polling"}),
        content_type="application/json",
    )
    assistant_message_id = first_message_response.json()["assistant_message"]["id"]

    status_response = client.get(reverse("api_v1:ai_assistant:ai-session-status-snapshot", args=[session_id]))
    assert status_response.status_code == 200
    assert status_response.json()["latest_assistant_message_id"] == assistant_message_id
    assert status_response.json()["latest_assistant_message_status"] == "completed"
    assert status_response.json()["pending_assistant_messages"] == 0

    detail_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-message-detail", args=[session_id, assistant_message_id])
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == assistant_message_id
    assert detail_response.json()["status"] == "completed"

    incremental_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        {"after_id": first_message_response.json()["user_message"]["id"]},
    )
    assert incremental_response.status_code == 200
    assert [item["id"] for item in incremental_response.json()] == [assistant_message_id]


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER="local",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    AI_STREAM_POLL_INTERVAL_SECONDS=0,
    AI_STREAM_TIMEOUT_SECONDS=1,
)
def test_ai_sse_stream_returns_completed_message_and_done_event(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-ai-sse")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima rumoroso")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]
    message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Avvia stream completato"}),
        content_type="application/json",
    )
    assistant_message_id = message_response.json()["assistant_message"]["id"]

    stream_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-message-stream", args=[session_id, assistant_message_id])
    )

    assert stream_response.status_code == 200
    assert stream_response["Content-Type"].startswith("text/event-stream")
    payload = b"".join(stream_response.streaming_content).decode()
    assert "event: message" in payload
    assert '"status": "completed"' in payload
    assert "event: done" in payload


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER="local",
    CELERY_TASK_ALWAYS_EAGER=False,
    CELERY_TASK_EAGER_PROPAGATES=True,
    AI_STREAM_POLL_INTERVAL_SECONDS=0,
    AI_STREAM_TIMEOUT_SECONDS=0,
)
def test_ai_sse_stream_can_timeout_for_queued_message(client, monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-sse-timeout")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)

    from apps.ai_assistant import views

    monkeypatch.setattr(views.generate_ai_reply_task, "delay", lambda message_id: None)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]
    message_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Avvia stream timeout"}),
        content_type="application/json",
    )
    assistant_message_id = message_response.json()["assistant_message"]["id"]

    stream_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-message-stream", args=[session_id, assistant_message_id])
    )

    assert stream_response.status_code == 200
    payload = b"".join(stream_response.streaming_content).decode()
    assert '"status": "queued"' in payload
    assert "event: timeout" in payload


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local")
def test_generate_ai_reply_task_persists_chunked_content(monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Idraulica", slug="idraulica-ai-chunks")
    case = Case.objects.create(customer_user=customer, category=category, title="Perdita sotto lavello")
    session = customer.ai_sessions.create(case=case)
    AiMessage.objects.create(session=session, role=AiMessage.Roles.USER, content="Cosa controllo?")
    assistant_message = AiMessage.objects.create(
        session=session,
        role=AiMessage.Roles.ASSISTANT,
        content="",
        status=AiMessage.Statuses.QUEUED,
    )

    class FakeProvider:
        def stream_reply(self, session, messages):
            yield "Prima parte. "
            yield "Seconda parte."

    monkeypatch.setattr("apps.ai_assistant.tasks.get_ai_provider", lambda: FakeProvider())

    result = generate_ai_reply_task(assistant_message.id)

    assistant_message.refresh_from_db()
    assert result["status"] == "completed"
    assert assistant_message.status == AiMessage.Statuses.COMPLETED
    assert assistant_message.content == "Prima parte. Seconda parte."


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local")
def test_generate_ai_diagnostic_reply_task_persists_structured_snapshot(monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-task-diagnostic")
    case = Case.objects.create(customer_user=customer, category=category, title="Presa calda")
    session = customer.ai_sessions.create(case=case)
    AiMessage.objects.create(session=session, role=AiMessage.Roles.USER, content="La presa e' calda")
    assistant_message = AiMessage.objects.create(
        session=session,
        role=AiMessage.Roles.ASSISTANT,
        content="",
        status=AiMessage.Statuses.QUEUED,
    )

    class FakeProvider:
        def build_diagnostic_reply(self, session, messages):
            return {
                "assistant_response": "Serve cautela e verifica professionale.",
                "case_summary": "Presa calda segnalata dall'utente.",
                "risk_level": "high",
                "next_question": "Il calore resta anche senza carichi collegati?",
                "escalation_recommended": True,
                "escalation_reason": "Possibile surriscaldamento.",
                "recommendation": "Non usare la presa fino a verifica.",
                "facts": {"asset": "presa"},
                "safety_notes": ["Non smontare la presa."],
            }

    monkeypatch.setattr("apps.ai_assistant.tasks.get_ai_provider", lambda: FakeProvider())

    result = generate_ai_diagnostic_reply_task(assistant_message.id)

    assistant_message.refresh_from_db()
    snapshot = AiDiagnosticSnapshot.objects.get(session=session)
    assert result["status"] == "completed"
    assert result["diagnostic_snapshot_id"] == snapshot.id
    assert assistant_message.status == AiMessage.Statuses.COMPLETED
    assert assistant_message.content == "Serve cautela e verifica professionale."
    assert assistant_message.metadata_json["diagnostic"]["risk_level"] == "high"
    assert snapshot.risk_level == "high"
    assert snapshot.next_question == "Il calore resta anche senza carichi collegati?"


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local")
def test_generate_ai_reply_task_clears_partial_content_when_chunked_provider_fails(monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Idraulica", slug="idraulica-ai-failure")
    case = Case.objects.create(customer_user=customer, category=category, title="Perdita sotto lavello")
    session = customer.ai_sessions.create(case=case)
    AiMessage.objects.create(session=session, role=AiMessage.Roles.USER, content="Cosa controllo?")
    assistant_message = AiMessage.objects.create(
        session=session,
        role=AiMessage.Roles.ASSISTANT,
        content="",
        status=AiMessage.Statuses.QUEUED,
    )

    class FakeProvider:
        def stream_reply(self, session, messages):
            yield "Parziale "
            raise Exception("boom")

    def fake_get_ai_provider():
        class WrappedProvider:
            def stream_reply(self, session, messages):
                try:
                    yield from FakeProvider().stream_reply(session, messages)
                except Exception as exc:
                    from apps.ai_assistant.provider import AiProviderError

                    raise AiProviderError("OpenAI provider request failed.") from exc

        return WrappedProvider()

    monkeypatch.setattr("apps.ai_assistant.tasks.get_ai_provider", fake_get_ai_provider)

    result = generate_ai_reply_task(assistant_message.id)

    assistant_message.refresh_from_db()
    assert result["status"] == "failed"
    assert assistant_message.status == AiMessage.Statuses.FAILED
    assert assistant_message.content == ""
    assert assistant_message.error_detail == "OpenAI provider request failed."


@pytest.mark.django_db
@override_settings(
    AI_PROVIDER="local",
    AI_STREAM_POLL_INTERVAL_SECONDS=0,
    AI_STREAM_TIMEOUT_SECONDS=1,
)
def test_ai_sse_stream_emits_delta_events_when_message_content_grows(client, monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-ai-sse-delta")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima rumoroso")
    session = customer.ai_sessions.create(case=case)
    assistant_message = AiMessage.objects.create(
        session=session,
        role=AiMessage.Roles.ASSISTANT,
        content="",
        status=AiMessage.Statuses.QUEUED,
    )
    client.force_login(customer)

    updates = iter(
        [
            (AiMessage.Statuses.PROCESSING, "Prima parte"),
            (AiMessage.Statuses.COMPLETED, "Prima parte finale"),
        ]
    )

    def fake_sleep(_seconds):
        try:
            status_value, content_value = next(updates)
        except StopIteration:
            return None
        AiMessage.objects.filter(id=assistant_message.id).update(status=status_value, content=content_value)
        return None

    monkeypatch.setattr("apps.ai_assistant.views.time.sleep", fake_sleep)

    stream_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-message-stream", args=[session.id, assistant_message.id])
    )

    payload = b"".join(stream_response.streaming_content).decode()
    assert "event: delta" in payload
    assert '"delta": " finale"' in payload
    assert '"status": "completed"' in payload


@pytest.mark.django_db
@override_settings(AI_PROVIDER="local", CELERY_TASK_ALWAYS_EAGER=False, CELERY_TASK_EAGER_PROPAGATES=True)
def test_ai_message_flow_rejects_new_user_message_while_reply_is_pending(client, monkeypatch):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-ai-lock")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    client.force_login(customer)

    from apps.ai_assistant import views

    monkeypatch.setattr(views.generate_ai_reply_task, "delay", lambda message_id: None)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    first_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Primo messaggio"}),
        content_type="application/json",
    )
    assert first_response.status_code == 202
    assert first_response.json()["assistant_message"]["status"] == "queued"

    second_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        data=json.dumps({"content": "Secondo messaggio"}),
        content_type="application/json",
    )
    assert second_response.status_code == 400
    assert second_response.json() == {
        "session": ["An assistant reply is already pending for this session."]
    }


@pytest.mark.django_db
def test_ai_polling_endpoints_validate_query_params(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-ai-query")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima rumoroso")
    client.force_login(customer)

    session_response = client.post(
        reverse("api_v1:ai_assistant:ai-session-list"),
        data=json.dumps({"case_id": case.id}),
        content_type="application/json",
    )
    session_id = session_response.json()["id"]

    invalid_limit_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        {"limit": "not-a-number"},
    )
    assert invalid_limit_response.status_code == 400
    assert "limit" in invalid_limit_response.json()

    invalid_after_response = client.get(
        reverse("api_v1:ai_assistant:ai-session-messages", args=[session_id]),
        {"after_id": 0},
    )
    assert invalid_after_response.status_code == 400
    assert "after_id" in invalid_after_response.json()
