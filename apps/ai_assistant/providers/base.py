import json
from typing import Protocol


class AiProviderError(Exception):
    pass


class BaseAiProvider(Protocol):
    provider_name: str

    def build_reply(self, session, messages):
        raise NotImplementedError

    def build_diagnostic_reply(self, session, messages):
        raise NotImplementedError

    def stream_reply(self, session, messages):
        reply = self.build_reply(session, messages)
        yield reply


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
        "excluded_facts": payload.get("excluded_facts") if isinstance(payload.get("excluded_facts"), dict) else {},
        "asked_questions": (
            [clean_text(item) for item in payload.get("asked_questions", []) if clean_text(item)]
            if isinstance(payload.get("asked_questions"), list)
            else []
        ),
        "safety_notes": safety_notes,
    }
    if not normalized["assistant_response"]:
        normalized["assistant_response"] = (
            normalized["next_question"]
            or normalized["recommendation"]
            or "Ho aggiornato il riepilogo della pratica."
        )
    return normalized
