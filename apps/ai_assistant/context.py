import json
from decimal import Decimal

from django.conf import settings

from .models import AiContextDigest, AiDiagnosticSnapshot, AiMessage


def estimate_token_count(value) -> int:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=True, sort_keys=True)
    if not text:
        return 0
    return max((len(text) + 3) // 4, 1)


def estimate_cost(input_tokens: int = 0, output_tokens: int = 0) -> Decimal:
    input_cost_per_1k = Decimal(str(getattr(settings, "AI_ESTIMATED_INPUT_COST_PER_1K_TOKENS", 0)))
    output_cost_per_1k = Decimal(str(getattr(settings, "AI_ESTIMATED_OUTPUT_COST_PER_1K_TOKENS", 0)))
    return ((Decimal(input_tokens) * input_cost_per_1k) + (Decimal(output_tokens) * output_cost_per_1k)) / Decimal(1000)


def get_latest_context_digest(session):
    return session.context_digests.order_by("-to_message_id", "-created_at", "-id").first()


def should_compact_context(session, threshold: int | None = None) -> bool:
    threshold = threshold or int(getattr(settings, "AI_CONTEXT_COMPACTION_MESSAGE_THRESHOLD", 8))
    if threshold <= 0:
        return False

    latest_digest = get_latest_context_digest(session)
    queryset = session.messages.filter(status=AiMessage.Statuses.COMPLETED)
    if latest_digest is not None and latest_digest.to_message_id is not None:
        queryset = queryset.filter(id__gt=latest_digest.to_message_id)
    return queryset.count() >= threshold


def build_digest_summary(session, snapshot, messages):
    parts = []
    if session.case_id is not None:
        parts.append(f"Pratica #{session.case_id}: {session.case.title}.")
    if snapshot is not None and snapshot.summary:
        parts.append(snapshot.summary)

    user_messages = [message.content.strip() for message in messages if message.role == AiMessage.Roles.USER]
    if user_messages:
        recent_user_messages = user_messages[-3:]
        parts.append("Ultime informazioni utente: " + " | ".join(recent_user_messages))
    return " ".join(part for part in parts if part).strip()


def compact_ai_context(session, trigger_reason: str = "threshold", force: bool = False):
    if not force and not should_compact_context(session):
        return None

    latest_digest = get_latest_context_digest(session)
    messages_queryset = session.messages.filter(status=AiMessage.Statuses.COMPLETED).order_by("created_at", "id")
    if latest_digest is not None and latest_digest.to_message_id is not None:
        messages_queryset = messages_queryset.filter(id__gt=latest_digest.to_message_id)

    messages = list(messages_queryset)
    if not messages:
        return None

    try:
        snapshot = session.diagnostic_snapshot
    except AiDiagnosticSnapshot.DoesNotExist:
        snapshot = None

    summary = build_digest_summary(session, snapshot, messages)
    facts = snapshot.facts_json if snapshot is not None and isinstance(snapshot.facts_json, dict) else {}
    excluded_facts = (
        snapshot.excluded_facts_json
        if snapshot is not None and isinstance(snapshot.excluded_facts_json, dict)
        else {}
    )
    asked_questions = (
        snapshot.asked_questions_json
        if snapshot is not None and isinstance(snapshot.asked_questions_json, list)
        else []
    )
    safety_notes = (
        snapshot.safety_notes_json
        if snapshot is not None and isinstance(snapshot.safety_notes_json, list)
        else []
    )

    digest_payload = {
        "summary": summary,
        "facts": facts,
        "excluded_facts": excluded_facts,
        "asked_questions": asked_questions,
        "safety_notes": safety_notes,
        "risk_level": snapshot.risk_level if snapshot is not None else "unknown",
    }
    estimated_input_tokens = estimate_token_count([{"role": message.role, "content": message.content} for message in messages])
    estimated_output_tokens = estimate_token_count(digest_payload)

    digest = AiContextDigest.objects.create(
        session=session,
        from_message=messages[0],
        to_message=messages[-1],
        source_snapshot=snapshot,
        summary=summary,
        risk_level=snapshot.risk_level if snapshot is not None else "unknown",
        facts_json=facts,
        excluded_facts_json=excluded_facts,
        asked_questions_json=asked_questions,
        safety_notes_json=safety_notes,
        message_count=len(messages),
        total_completed_messages=session.messages.filter(status=AiMessage.Statuses.COMPLETED).count(),
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
        estimated_cost=estimate_cost(estimated_input_tokens, estimated_output_tokens),
        trigger_reason=trigger_reason,
        metadata_json={
            "previous_digest_id": latest_digest.id if latest_digest is not None else None,
            "strategy": "deterministic_snapshot_digest",
        },
    )

    if snapshot is not None:
        snapshot.compacted_summary = summary
        snapshot.context_version += 1
        snapshot.context_metadata_json = {
            **snapshot.context_metadata_json,
            "latest_context_digest_id": digest.id,
            "latest_context_digest_to_message_id": digest.to_message_id,
        }
        snapshot.save(update_fields=["compacted_summary", "context_version", "context_metadata_json", "updated_at"])

    return digest
