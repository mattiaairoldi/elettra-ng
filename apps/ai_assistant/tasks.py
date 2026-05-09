from celery import shared_task

from apps.cases.events import create_case_event
from apps.cases.models import Case, CaseEvent

from .context import compact_ai_context
from .models import AiDiagnosticSnapshot, AiMessage
from .providers import (
    AiProviderError,
    build_diagnostic_context,
    build_diagnostic_provider_messages,
    build_provider_messages,
    get_ai_provider,
    normalize_diagnostic_payload,
)
from .questions import append_unique_diagnostic_questions
from .usage import AiUsageLimitExceeded, enforce_ai_usage_limits, record_ai_usage


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
        enforce_ai_usage_limits(assistant_message.session, purpose="chat")
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
    except (AiProviderError, AiUsageLimitExceeded) as exc:
        assistant_message.content = ""
        assistant_message.status = AiMessage.Statuses.FAILED
        assistant_message.error_detail = str(exc)
        assistant_message.save(update_fields=["content", "status", "error_detail"])
        return {"status": assistant_message.status, "error_detail": assistant_message.error_detail}

    assistant_message.content = reply
    assistant_message.status = AiMessage.Statuses.COMPLETED
    assistant_message.error_detail = ""
    assistant_message.save(update_fields=["content", "status", "error_detail"])
    record_ai_usage(
        session=assistant_message.session,
        message=assistant_message,
        purpose="chat",
        provider=provider,
        input_payload=provider_messages,
        output_payload=reply,
        metadata={"provider_message_count": len(provider_messages)},
    )
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

    provider_messages = build_diagnostic_provider_messages(assistant_message.session)
    context = build_diagnostic_context(assistant_message.session)
    try:
        enforce_ai_usage_limits(
            assistant_message.session,
            purpose="diagnostic",
            check_case_turn_limit=False,
        )
        provider = get_ai_provider()
        raw_payload = provider.build_diagnostic_reply(assistant_message.session, provider_messages)
        payload = normalize_diagnostic_payload(raw_payload)
    except (AiProviderError, AiUsageLimitExceeded) as exc:
        assistant_message.content = ""
        assistant_message.status = AiMessage.Statuses.FAILED
        assistant_message.error_detail = str(exc)
        assistant_message.metadata_json = {"diagnostic": {"status": "failed"}}
        assistant_message.save(update_fields=["content", "status", "error_detail", "metadata_json"])
        return {"status": assistant_message.status, "error_detail": assistant_message.error_detail}

    try:
        existing_snapshot = assistant_message.session.diagnostic_snapshot
    except AiDiagnosticSnapshot.DoesNotExist:
        existing_snapshot = None
    previous_facts = existing_snapshot.facts_json if existing_snapshot is not None else {}
    previous_excluded_facts = existing_snapshot.excluded_facts_json if existing_snapshot is not None else {}
    previous_asked_questions = existing_snapshot.asked_questions_json if existing_snapshot is not None else []
    if not isinstance(previous_facts, dict):
        previous_facts = {}
    if not isinstance(previous_excluded_facts, dict):
        previous_excluded_facts = {}
    if not isinstance(previous_asked_questions, list):
        previous_asked_questions = []

    facts = {**previous_facts, **payload["facts"]}
    excluded_facts = {**previous_excluded_facts, **payload["excluded_facts"]}
    asked_questions = append_unique_diagnostic_questions(
        previous_asked_questions,
        [*payload["asked_questions"], payload["next_question"]],
    )

    latest_user_message = (
        assistant_message.session.messages.filter(role=AiMessage.Roles.USER)
        .order_by("-created_at", "-id")
        .first()
    )
    selection = {}
    if latest_user_message is not None:
        selection = latest_user_message.metadata_json.get("diagnostic", {})
        if not isinstance(selection, dict):
            selection = {}

    diagnostic_chapter_id = selection.get("diagnostic_chapter_id")
    diagnostic_chapter_option_id = selection.get("diagnostic_chapter_option_id")
    if existing_snapshot is not None:
        diagnostic_chapter_id = diagnostic_chapter_id or existing_snapshot.diagnostic_chapter_id
        diagnostic_chapter_option_id = diagnostic_chapter_option_id or existing_snapshot.diagnostic_chapter_option_id

    context_metadata = {
        **context["metadata"],
        "strategy": "snapshot_recent_messages",
        "provider_message_count": len(provider_messages),
    }

    assistant_message.content = payload["assistant_response"]
    assistant_message.status = AiMessage.Statuses.COMPLETED
    assistant_message.error_detail = ""
    assistant_message.metadata_json = {"diagnostic": {**payload, "context_metadata": context_metadata}}
    assistant_message.save(update_fields=["content", "status", "error_detail", "metadata_json"])
    usage = record_ai_usage(
        session=assistant_message.session,
        message=assistant_message,
        purpose="diagnostic",
        provider=provider,
        input_payload=provider_messages,
        output_payload=payload,
        metadata={
            "provider_message_count": len(provider_messages),
            "context_strategy": context_metadata["strategy"],
        },
    )

    snapshot, _created = AiDiagnosticSnapshot.objects.update_or_create(
        session=assistant_message.session,
        defaults={
            "diagnostic_chapter_id": diagnostic_chapter_id,
            "diagnostic_chapter_option_id": diagnostic_chapter_option_id,
            "source_message": assistant_message,
            "summary": payload["case_summary"],
            "risk_level": payload["risk_level"],
            "next_question": payload["next_question"],
            "escalation_recommended": payload["escalation_recommended"],
            "escalation_reason": payload["escalation_reason"],
            "recommendation": payload["recommendation"],
            "facts_json": facts,
            "excluded_facts_json": excluded_facts,
            "asked_questions_json": asked_questions,
            "safety_notes_json": payload["safety_notes"],
            "context_metadata_json": context_metadata,
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
            "ai_usage_ledger_id": usage.id,
        },
    )
    digest = compact_ai_context(assistant_message.session, trigger_reason="threshold")
    return {
        "status": assistant_message.status,
        "assistant_message_id": assistant_message.id,
        "diagnostic_snapshot_id": snapshot.id,
        "context_digest_id": digest.id if digest is not None else None,
    }


@shared_task
def compact_ai_context_task(session_id, force=False, trigger_reason="manual"):
    from .models import AiSession

    session = (
        AiSession.objects.select_related("case", "case__category")
        .prefetch_related("messages", "context_digests")
        .get(id=session_id)
    )
    digest = compact_ai_context(session, trigger_reason=trigger_reason, force=force)
    if digest is None:
        return {"status": "skipped", "session_id": session.id}
    return {"status": "completed", "session_id": session.id, "context_digest_id": digest.id}
