import json

from django.conf import settings

from apps.appointments.models import Appointment
from apps.cases.models import Case

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AiProviderError(Exception):
    pass


DIAGNOSTIC_RISK_LEVELS = {"unknown", "low", "medium", "high", "urgent"}


def clean_text(value):
    return str(value or "").strip()


def coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "si", "on"}
    return bool(value)


def parse_json_object(raw_value):
    if isinstance(raw_value, dict):
        return raw_value
    if not isinstance(raw_value, str):
        raise AiProviderError("AI provider returned an invalid diagnostic payload.")

    cleaned = raw_value.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise AiProviderError("AI provider returned non-JSON diagnostic output.") from None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AiProviderError("AI provider returned invalid diagnostic JSON.") from exc

    if not isinstance(parsed, dict):
        raise AiProviderError("AI provider returned an invalid diagnostic payload.")
    return parsed


def normalize_diagnostic_payload(raw_payload):
    payload = parse_json_object(raw_payload)
    risk_level = clean_text(payload.get("risk_level")).lower() or "unknown"
    if risk_level not in DIAGNOSTIC_RISK_LEVELS:
        risk_level = "unknown"

    facts = payload.get("facts")
    if not isinstance(facts, dict):
        facts = {}

    safety_notes = payload.get("safety_notes")
    if isinstance(safety_notes, list):
        safety_notes = [clean_text(item) for item in safety_notes if clean_text(item)]
    elif clean_text(safety_notes):
        safety_notes = [clean_text(safety_notes)]
    else:
        safety_notes = []

    normalized = {
        "assistant_response": clean_text(payload.get("assistant_response")),
        "case_summary": clean_text(payload.get("case_summary") or payload.get("summary")),
        "risk_level": risk_level,
        "next_question": clean_text(payload.get("next_question")),
        "escalation_recommended": coerce_bool(payload.get("escalation_recommended")),
        "escalation_reason": clean_text(payload.get("escalation_reason")),
        "recommendation": clean_text(payload.get("recommendation")),
        "facts": facts,
        "safety_notes": safety_notes,
    }
    if not normalized["assistant_response"]:
        normalized["assistant_response"] = (
            normalized["next_question"]
            or normalized["recommendation"]
            or "Ho aggiornato il riepilogo della pratica."
        )
    return normalized


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
    context = build_case_context(session)
    return (
        "Sei un assistente diagnostico per problemi tecnici domestici. "
        "Il tuo compito e' porre poche domande sicure, sintetizzare il caso e riconoscere quando serve un professionista. "
        "Non fornire istruzioni per aprire quadri elettrici, manipolare cavi, smontare componenti o fare misure su circuiti in tensione. "
        "Se emergono odore di bruciato, fumo, scintille, scosse, surriscaldamento o rischio elettrico, raccomanda di fermarsi e coinvolgere un professionista. "
        "Rispondi solo con un oggetto JSON valido con questi campi: "
        "assistant_response, case_summary, risk_level, next_question, escalation_recommended, escalation_reason, recommendation, facts, safety_notes. "
        "risk_level deve essere uno tra unknown, low, medium, high, urgent. "
        f"Contesto della pratica: {context}"
    )


class LocalAiProvider:
    def build_reply(self, session, messages):
        user_message = messages[-1]["content"].strip()
        parts = [f"Hai scritto: {user_message}"]
        if session.case_id is None:
            parts.append("Questa sessione non e' collegata a una pratica specifica.")
            parts.append("Descrivi categoria del problema, sintomi e cosa hai gia' verificato.")
            return " ".join(parts)

        context = build_case_context(session)
        parts.append(context)
        if session.case.status == Case.Statuses.IN_DIAGNOSIS:
            parts.append("Continua con verifiche sicure e non invasive prima di escalare.")
        return " ".join(parts)

    def stream_reply(self, session, messages):
        reply = self.build_reply(session, messages)
        for chunk in reply.split():
            yield f"{chunk} "

    def build_diagnostic_reply(self, session, messages):
        user_message = clean_text(messages[-1]["content"] if messages else "")
        lowered = user_message.lower()
        category = session.case.category.name if session.case_id is not None else "problema domestico"

        danger_terms = {
            "odore di bruciato",
            "bruciato",
            "fumo",
            "scintille",
            "scossa",
            "surriscalda",
            "caldo",
        }
        electrical_terms = {"salvavita", "corrente", "presa", "luce", "quadro", "interruttore"}

        if any(term in lowered for term in danger_terms):
            return {
                "assistant_response": (
                    "La descrizione indica un possibile rischio. Evita verifiche invasive e coinvolgi un professionista."
                ),
                "case_summary": f"Problema {category}: {user_message}",
                "risk_level": "urgent",
                "next_question": "Ci sono fumo, scintille o odore persistente anche dopo aver smesso di usare l'impianto?",
                "escalation_recommended": True,
                "escalation_reason": "Segnali compatibili con rischio elettrico o surriscaldamento.",
                "recommendation": "Mettere in sicurezza la situazione e richiedere supporto professionale.",
                "facts": {"reported_issue": user_message, "category": category},
                "safety_notes": ["Non aprire quadri o componenti elettrici.", "Non manipolare cavi o parti in tensione."],
            }

        if any(term in lowered for term in electrical_terms):
            return {
                "assistant_response": "Ho aggiornato il quadro del problema. Procediamo con una sola domanda di chiarimento.",
                "case_summary": f"Problema {category}: {user_message}",
                "risk_level": "medium",
                "next_question": "Il problema riguarda un solo punto della casa o piu' stanze/utenze?",
                "escalation_recommended": False,
                "escalation_reason": "",
                "recommendation": "Raccogliere ancora informazioni senza eseguire interventi tecnici.",
                "facts": {"reported_issue": user_message, "category": category},
                "safety_notes": ["Limitarsi a osservazioni esterne e sicure."],
            }

        return {
            "assistant_response": "Ho registrato la descrizione. Mi serve un dettaglio per classificare meglio il problema.",
            "case_summary": f"Problema {category}: {user_message}",
            "risk_level": "unknown",
            "next_question": "Da quando si presenta il problema e cosa stava succedendo quando e' comparso?",
            "escalation_recommended": False,
            "escalation_reason": "",
            "recommendation": "Continuare la raccolta di informazioni.",
            "facts": {"reported_issue": user_message, "category": category},
            "safety_notes": [],
        }


class OpenAIAiProvider:
    def __init__(self):
        if OpenAI is None:
            raise AiProviderError("OpenAI SDK is not installed.")

        api_key = getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise AiProviderError("OPENAI_API_KEY is not configured.")

        client_kwargs = {
            "api_key": api_key,
            "base_url": "https://api.openai.com/v1",
        }
        base_url = getattr(settings, "OPENAI_BASE_URL", "")
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)
        self.model = getattr(settings, "AI_OPENAI_MODEL", "gpt-5.4-mini")

    def build_reply(self, session, messages):
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=build_ai_instructions(session),
                input=messages,
                store=False,
            )
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        reply = getattr(response, "output_text", "") or ""
        reply = reply.strip()
        if not reply:
            raise AiProviderError("OpenAI provider returned an empty response.")
        return reply

    def stream_reply(self, session, messages):
        try:
            stream = self.client.responses.create(
                model=self.model,
                instructions=build_ai_instructions(session),
                input=messages,
                store=False,
                stream=True,
            )
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        emitted = False
        try:
            for event in stream:
                if getattr(event, "type", "") == "response.output_text.delta":
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        emitted = True
                        yield delta
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        if not emitted:
            raise AiProviderError("OpenAI provider returned an empty response.")

    def build_diagnostic_reply(self, session, messages):
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=build_diagnostic_instructions(session),
                input=messages,
                store=False,
            )
        except Exception as exc:
            raise AiProviderError("OpenAI provider request failed.") from exc

        reply = getattr(response, "output_text", "") or ""
        if not reply.strip():
            raise AiProviderError("OpenAI provider returned an empty diagnostic response.")
        return normalize_diagnostic_payload(reply)


def build_provider_messages(session):
    return [
        {"role": message.role, "content": message.content}
        for message in session.messages.order_by("created_at", "id")
        if message.role in {"user", "assistant", "system"} and message.status == message.Statuses.COMPLETED
    ]


def get_ai_provider():
    provider_name = getattr(settings, "AI_PROVIDER", "local")
    if provider_name == "local":
        return LocalAiProvider()
    if provider_name == "openai":
        return OpenAIAiProvider()
    raise AiProviderError(f"Unsupported AI provider: {provider_name}")
