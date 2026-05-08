from celery import shared_task

from apps.cases.events import create_case_event
from apps.cases.models import Case, CaseEvent

from .models import AiDiagnosticSnapshot, AiMessage
from .provider import AiProviderError, build_provider_messages, get_ai_provider, normalize_diagnostic_payload


@shared_task
def generate_ai_reply_task(assistant_message_id):
    assistant_message = (
        AiMessage.objects.select_related(
            "session",
            "session__case",
            "session__case__category",
            "session__case__assigned_professional",
            "session__case__current_diagnostic_node",
        )
        .prefetch_related("session__messages", "session__case__appointments")
        .get(id=assistant_message_id, role=AiMessage.Roles.ASSISTANT)
    )
    assistant_message.status = AiMessage.Statuses.PROCESSING
    assistant_message.error_detail = ""
    assistant_message.save(update_fields=["status", "error_detail"])

    provider_messages = build_provider_messages(assistant_message.session)
    try:
        provider = get_ai_provider()
        reply_parts = []
        if hasattr(provider, "stream_reply"):
            for chunk in provider.stream_reply(assistant_message.session, provider_messages):
                if not chunk:
                    continue
                reply_parts.append(chunk)
                assistant_message.content = "".join(reply_parts).strip()
                assistant_message.save(update_fields=["content"])
            reply = "".join(reply_parts).strip()
        else:
            reply = provider.build_reply(assistant_message.session, provider_messages)
        if not reply:
            raise AiProviderError("AI provider returned an empty response.")
    except AiProviderError as exc:
        assistant_message.content = ""
        assistant_message.status = AiMessage.Statuses.FAILED
        assistant_message.error_detail = str(exc)
        assistant_message.save(update_fields=["content", "status", "error_detail"])
        return {"status": assistant_message.status, "error_detail": assistant_message.error_detail}

    assistant_message.content = reply
    assistant_message.status = AiMessage.Statuses.COMPLETED
    assistant_message.error_detail = ""
    assistant_message.save(update_fields=["content", "status", "error_detail"])
    return {"status": assistant_message.status, "assistant_message_id": assistant_message.id}


@shared_task
def generate_ai_diagnostic_reply_task(assistant_message_id):
    assistant_message = (
        AiMessage.objects.select_related(
            "session",
            "session__user",
            "session__case",
            "session__case__category",
            "session__case__assigned_professional",
            "session__case__current_diagnostic_node",
        )
        .prefetch_related("session__messages", "session__case__appointments")
        .get(id=assistant_message_id, role=AiMessage.Roles.ASSISTANT)
    )
    assistant_message.status = AiMessage.Statuses.PROCESSING
    assistant_message.error_detail = ""
    assistant_message.save(update_fields=["status", "error_detail"])

    provider_messages = build_provider_messages(assistant_message.session)
    try:
        provider = get_ai_provider()
        raw_payload = provider.build_diagnostic_reply(assistant_message.session, provider_messages)
        payload = normalize_diagnostic_payload(raw_payload)
    except AiProviderError as exc:
        assistant_message.content = ""
        assistant_message.status = AiMessage.Statuses.FAILED
        assistant_message.error_detail = str(exc)
        assistant_message.metadata_json = {"diagnostic": {"status": "failed"}}
        assistant_message.save(update_fields=["content", "status", "error_detail", "metadata_json"])
        return {"status": assistant_message.status, "error_detail": assistant_message.error_detail}

    assistant_message.content = payload["assistant_response"]
    assistant_message.status = AiMessage.Statuses.COMPLETED
    assistant_message.error_detail = ""
    assistant_message.metadata_json = {"diagnostic": payload}
    assistant_message.save(update_fields=["content", "status", "error_detail", "metadata_json"])

    snapshot, _created = AiDiagnosticSnapshot.objects.update_or_create(
        session=assistant_message.session,
        defaults={
            "source_message": assistant_message,
            "summary": payload["case_summary"],
            "risk_level": payload["risk_level"],
            "next_question": payload["next_question"],
            "escalation_recommended": payload["escalation_recommended"],
            "escalation_reason": payload["escalation_reason"],
            "recommendation": payload["recommendation"],
            "facts_json": payload["facts"],
            "safety_notes_json": payload["safety_notes"],
            "raw_payload_json": payload,
        },
    )

    case = assistant_message.session.case
    previous_status = case.status
    if case.status == Case.Statuses.OPEN:
        case.status = Case.Statuses.IN_DIAGNOSIS
        case.save(update_fields=["status", "updated_at"])

    create_case_event(
        case=case,
        event_type=CaseEvent.EventTypes.AI_DIAGNOSTIC_PROGRESS,
        actor_user=assistant_message.session.user,
        payload={
            "ai_session_id": assistant_message.session_id,
            "assistant_message_id": assistant_message.id,
            "diagnostic_snapshot_id": snapshot.id,
            "previous_status": previous_status,
            "status": case.status,
            "risk_level": snapshot.risk_level,
            "escalation_recommended": snapshot.escalation_recommended,
        },
    )
    return {
        "status": assistant_message.status,
        "assistant_message_id": assistant_message.id,
        "diagnostic_snapshot_id": snapshot.id,
    }
