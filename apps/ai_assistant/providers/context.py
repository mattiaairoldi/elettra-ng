import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.appointments.models import Appointment
from apps.cases.models import Case

from ..context import estimate_token_count, get_latest_context_digest


def get_diagnostic_snapshot(session):
    try:
        return session.diagnostic_snapshot
    except ObjectDoesNotExist:
        return None


def get_latest_diagnostic_selection(session):
    latest_user_message = (
        session.messages.filter(role="user")
        .exclude(metadata_json={})
        .order_by("-created_at", "-id")
        .first()
    )
    if latest_user_message is None:
        return {}
    diagnostic_metadata = latest_user_message.metadata_json.get("diagnostic", {})
    return diagnostic_metadata if isinstance(diagnostic_metadata, dict) else {}


def build_safety_rule_context(chapter, latest_selection):
    if chapter is not None:
        return [
            {
                "title": rule.title,
                "trigger_terms": rule.trigger_terms_json,
                "guidance": rule.guidance,
                "risk_level": rule.risk_level,
                "escalation_level": rule.escalation_level,
            }
            for rule in chapter.safety_rules.filter(is_active=True).order_by("sort_order", "id")
        ]
    safety_rules = latest_selection.get("diagnostic_chapter_safety_rules", [])
    return safety_rules if isinstance(safety_rules, list) else []


def build_diagnostic_context(session):
    snapshot = get_diagnostic_snapshot(session)
    latest_selection = get_latest_diagnostic_selection(session)
    latest_digest = get_latest_context_digest(session)

    chapter = getattr(snapshot, "diagnostic_chapter", None) if snapshot is not None else None
    option = getattr(snapshot, "diagnostic_chapter_option", None) if snapshot is not None else None

    chapter_context = {
        "id": getattr(chapter, "id", latest_selection.get("diagnostic_chapter_id")),
        "name": getattr(chapter, "name", latest_selection.get("diagnostic_chapter_name", "")),
        "slug": getattr(chapter, "slug", latest_selection.get("diagnostic_chapter_slug", "")),
        "prompt_context": getattr(chapter, "prompt_context", latest_selection.get("diagnostic_chapter_prompt_context", "")),
        "safety_context": getattr(chapter, "safety_context", latest_selection.get("diagnostic_chapter_safety_context", "")),
        "safety_rules": build_safety_rule_context(chapter, latest_selection),
    }
    option_context = {
        "id": getattr(option, "id", latest_selection.get("diagnostic_chapter_option_id")),
        "label": getattr(option, "label", latest_selection.get("diagnostic_chapter_option_label", "")),
        "slug": getattr(option, "slug", latest_selection.get("diagnostic_chapter_option_slug", "")),
        "option_type": getattr(option, "option_type", latest_selection.get("diagnostic_chapter_option_type", "")),
        "prompt_hint": getattr(option, "prompt_hint", latest_selection.get("diagnostic_chapter_option_prompt_hint", "")),
    }

    completed_messages = session.messages.filter(status="completed").order_by("created_at", "id")
    recent_queryset = completed_messages
    if latest_digest is not None and latest_digest.to_message_id is not None:
        recent_queryset = recent_queryset.filter(id__gt=latest_digest.to_message_id)
    recent_limit = max(int(getattr(settings, "AI_DIAGNOSTIC_RECENT_MESSAGES_LIMIT", 4)), 1)
    recent_messages = [
        {"role": message.role, "content": message.content}
        for message in recent_queryset.reverse()[:recent_limit]
    ]
    recent_messages.reverse()

    context = {
        "case": {
            "id": session.case_id,
            "status": session.case.status if session.case_id is not None else "",
            "category": session.case.category.name if session.case_id is not None else "",
            "title": session.case.title if session.case_id is not None else "",
            "description": session.case.description if session.case_id is not None else "",
        },
        "diagnostic": {
            "chapter": chapter_context,
            "option": option_context,
            "summary": snapshot.summary if snapshot is not None else "",
            "compacted_summary": (
                snapshot.compacted_summary
                if snapshot is not None and snapshot.compacted_summary
                else latest_digest.summary if latest_digest is not None else ""
            ),
            "risk_level": snapshot.risk_level if snapshot is not None else "unknown",
            "facts": snapshot.facts_json if snapshot is not None else {},
            "excluded_facts": snapshot.excluded_facts_json if snapshot is not None else {},
            "asked_questions": snapshot.asked_questions_json if snapshot is not None else [],
            "safety_notes": snapshot.safety_notes_json if snapshot is not None else [],
            "next_question": snapshot.next_question if snapshot is not None else "",
            "escalation_recommended": snapshot.escalation_recommended if snapshot is not None else False,
        },
        "latest_digest": {
            "id": latest_digest.id if latest_digest is not None else None,
            "to_message_id": latest_digest.to_message_id if latest_digest is not None else None,
            "summary": latest_digest.summary if latest_digest is not None else "",
            "risk_level": latest_digest.risk_level if latest_digest is not None else "unknown",
            "facts": latest_digest.facts_json if latest_digest is not None else {},
            "excluded_facts": latest_digest.excluded_facts_json if latest_digest is not None else {},
            "asked_questions": latest_digest.asked_questions_json if latest_digest is not None else [],
            "safety_notes": latest_digest.safety_notes_json if latest_digest is not None else [],
        },
        "recent_messages": recent_messages,
        "metadata": {
            "recent_message_limit": recent_limit,
            "recent_message_count": len(recent_messages),
            "total_completed_messages": completed_messages.count(),
            "compacted_summary_used": bool(
                (snapshot and snapshot.compacted_summary) or (latest_digest and latest_digest.summary)
            ),
            "latest_context_digest_id": latest_digest.id if latest_digest is not None else None,
            "context_version": snapshot.context_version if snapshot is not None else 1,
        },
    }
    context["metadata"]["estimated_context_tokens"] = estimate_token_count(
        {
            "case": context["case"],
            "diagnostic": context["diagnostic"],
            "latest_digest": context["latest_digest"],
            "recent_messages": context["recent_messages"],
        }
    )
    return context


def build_case_context(session):
    parts = []
    if session.case_id is None:
        parts.append("Nessuna pratica collegata.")
        return " ".join(parts)

    case = session.case
    parts.append(f"Pratica #{case.id}.")
    parts.append(f"Stato pratica: {case.status}.")
    parts.append(f"Categoria: {case.category.name}.")
    if case.title:
        parts.append(f"Titolo: {case.title}.")
    if case.description:
        parts.append(f"Descrizione: {case.description}.")
    if case.current_diagnostic_node_id is not None:
        parts.append(f"Nodo diagnostico corrente: {case.current_diagnostic_node.title}.")
    if case.assigned_professional_id is not None:
        professional_label = case.assigned_professional.get_full_name() or case.assigned_professional.email
        parts.append(f"Professionista assegnato: {professional_label}.")
    open_appointments = case.appointments.filter(
        status__in={
            Appointment.Statuses.REQUESTED,
            Appointment.Statuses.CONFIRMED,
            Appointment.Statuses.RESCHEDULED,
        }
    ).order_by("scheduled_start_at")
    if open_appointments.exists():
        appointment = open_appointments.first()
        parts.append(f"Prossimo appuntamento: {appointment.scheduled_start_at.isoformat()}.")
    elif case.status == Case.Statuses.WAITING_PROFESSIONAL:
        parts.append("La pratica e' in attesa di professionista o pianificazione.")
    elif case.status == Case.Statuses.IN_DIAGNOSIS:
        parts.append("La pratica e' in diagnosi guidata.")
    return " ".join(parts)


def build_ai_instructions(session):
    context = build_case_context(session)
    return (
        "Sei un assistente di supporto per problemi di casa. "
        "Rispondi in italiano, in modo pratico e prudente. "
        "Non inventare sopralluoghi, misure o stati non presenti nel contesto. "
        "Se il caso richiede operazioni pericolose o specialistiche, raccomanda di fermarsi e coinvolgere un professionista. "
        f"Contesto della pratica: {context}"
    )


def build_diagnostic_instructions(session):
    context = build_diagnostic_context(session)
    return (
        "Sei un assistente diagnostico per problemi tecnici domestici. "
        "Il tuo compito e' proporre un passaggio diagnostico chiaro per turno, anche con opzioni di risposta quando aiutano, sintetizzare il caso e riconoscere quando serve un professionista. "
        "Non fornire istruzioni per aprire quadri elettrici, manipolare cavi, smontare componenti o fare misure su circuiti in tensione. "
        "Se emergono odore di bruciato, fumo, scintille, scosse, surriscaldamento o rischio elettrico, raccomanda di fermarsi e coinvolgere un professionista. "
        "Rispondi solo con un oggetto JSON valido con questi campi: "
        "assistant_response, case_summary, risk_level, next_question, escalation_recommended, escalation_reason, recommendation, facts, excluded_facts, asked_questions, safety_notes. "
        "risk_level deve essere uno tra unknown, low, medium, high, urgent. "
        f"Contesto strutturato: {json.dumps(context, ensure_ascii=True)}"
    )


def build_provider_messages(session):
    return [
        {"role": message.role, "content": message.content}
        for message in session.messages.order_by("created_at", "id")
        if message.role in {"user", "assistant", "system"} and message.status == message.Statuses.COMPLETED
    ]


def build_diagnostic_provider_messages(session):
    recent_limit = max(int(getattr(settings, "AI_DIAGNOSTIC_RECENT_MESSAGES_LIMIT", 4)), 1)
    latest_digest = get_latest_context_digest(session)
    queryset = session.messages.filter(
        role__in={"user", "assistant", "system"},
        status="completed",
    )
    if latest_digest is not None and latest_digest.to_message_id is not None:
        queryset = queryset.filter(id__gt=latest_digest.to_message_id)
    messages = [
        {"role": message.role, "content": message.content}
        for message in queryset.order_by("-created_at", "-id")[:recent_limit]
    ]
    messages.reverse()
    return messages
