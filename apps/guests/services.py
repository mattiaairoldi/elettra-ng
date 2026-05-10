import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, Throttled

from apps.ai_assistant.models import AiDiagnosticSnapshot, AiMessage, AiSession, AiUsageLedger
from apps.cases.events import create_case_event
from apps.cases.models import Case, CaseEvent
from apps.organizations.services import get_or_create_personal_organization

from .models import GuestSession

User = get_user_model()

RISK_LEVEL_PRIORITY = {
    "low": Case.Priorities.LOW,
    "medium": Case.Priorities.NORMAL,
    "high": Case.Priorities.HIGH,
    "urgent": Case.Priorities.URGENT,
}


def _positive_int_setting(name: str, default: int) -> int:
    return max(int(getattr(settings, name, default)), 0)


def build_guest_token_hash(token: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_request_value_hash(value: str) -> str:
    if not value:
        return ""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_guest_token_from_request(request) -> str:
    header_token = request.headers.get("X-Guest-Token", "").strip()
    if header_token:
        return header_token

    authorization = request.headers.get("Authorization", "").strip()
    prefix = "Guest "
    if authorization.startswith(prefix):
        return authorization[len(prefix) :].strip()
    return ""


def build_guest_quotas(session: GuestSession) -> dict:
    ai_session = session.ai_sessions.filter(status="active").first()
    turns_used = 0
    messages_used = 0
    if ai_session is not None:
        turns_used = ai_session.messages.filter(role="user").count()
        messages_used = ai_session.messages.count()

    ai_turn_limit = _positive_int_setting("GUEST_AI_TURN_LIMIT", 2)
    message_limit = _positive_int_setting("GUEST_MESSAGE_LIMIT", 8)
    return {
        "ai_turn_limit": ai_turn_limit,
        "ai_turns_used": turns_used,
        "ai_turns_remaining": max(ai_turn_limit - turns_used, 0),
        "message_limit": message_limit,
        "messages_used": messages_used,
        "messages_remaining": max(message_limit - messages_used, 0),
    }


def create_guest_session(request) -> tuple[GuestSession, str]:
    token = secrets.token_urlsafe(32)
    ip_hash = build_request_value_hash(get_client_ip(request))
    user_agent_hash = build_request_value_hash(request.META.get("HTTP_USER_AGENT", ""))
    rate_limit = _positive_int_setting("GUEST_RATE_LIMIT_PER_IP_PER_DAY", 5)
    if ip_hash and rate_limit > 0:
        used_today = GuestSession.objects.filter(
            ip_hash=ip_hash,
            created_at__date=timezone.localdate(),
        ).count()
        if used_today >= rate_limit:
            raise Throttled(detail="Guest session daily limit reached for this network.")

    ttl_hours = _positive_int_setting("GUEST_SESSION_TTL_HOURS", 72) or 72
    session = GuestSession.objects.create(
        token_hash=build_guest_token_hash(token),
        expires_at=timezone.now() + timedelta(hours=ttl_hours),
        ip_hash=ip_hash,
        user_agent_hash=user_agent_hash,
    )
    return session, token


def authenticate_guest_session(request) -> GuestSession:
    token = get_guest_token_from_request(request)
    if not token:
        raise AuthenticationFailed("Guest token is required.")

    token_hash = build_guest_token_hash(token)
    try:
        session = GuestSession.objects.get(token_hash=token_hash)
    except GuestSession.DoesNotExist as exc:
        raise AuthenticationFailed("Invalid guest token.") from exc

    if session.expire_if_needed() or not session.is_usable:
        raise AuthenticationFailed("Guest session is not active.")
    return session


def _latest_guest_ai_session(session: GuestSession):
    return session.ai_sessions.filter(status=AiSession.Statuses.ACTIVE).first()


def _diagnostic_snapshot_for(ai_session):
    if ai_session is None:
        return None
    try:
        return AiDiagnosticSnapshot.objects.select_related(
            "diagnostic_chapter__category",
            "diagnostic_chapter_option",
        ).get(session=ai_session)
    except AiDiagnosticSnapshot.DoesNotExist:
        return None


def _latest_user_message(ai_session):
    if ai_session is None:
        return None
    return ai_session.messages.filter(role=AiMessage.Roles.USER).order_by("-created_at", "-id").first()


def _resolve_promotion_category(validated_data: dict, snapshot):
    category = validated_data.get("category")
    if category is not None:
        return category
    if snapshot is not None and snapshot.diagnostic_chapter is not None:
        return snapshot.diagnostic_chapter.category
    return None


def _build_promoted_case_title(validated_data: dict, snapshot, category) -> str:
    title = validated_data.get("case_title", "").strip()
    if title:
        return title[:200]
    if snapshot is not None and snapshot.diagnostic_chapter is not None:
        return f"Diagnosi ospite: {snapshot.diagnostic_chapter.name}"[:200]
    return f"Diagnosi ospite: {category.name}"[:200]


def _build_promoted_case_description(validated_data: dict, snapshot, latest_message) -> str:
    description = validated_data.get("case_description", "").strip()
    if description:
        return description

    parts = []
    if snapshot is not None:
        if snapshot.summary:
            parts.append(snapshot.summary)
        if snapshot.recommendation:
            parts.append(f"Indicazione: {snapshot.recommendation}")
        if snapshot.escalation_reason:
            parts.append(f"Motivo escalation: {snapshot.escalation_reason}")
    if parts:
        return "\n\n".join(parts)
    if latest_message is not None and latest_message.content.strip():
        return latest_message.content.strip()
    return "Pratica creata da una sessione diagnostica ospite."


def _build_promoted_case_priority(snapshot) -> str:
    if snapshot is None:
        return Case.Priorities.NORMAL
    return RISK_LEVEL_PRIORITY.get(snapshot.risk_level, Case.Priorities.NORMAL)


@transaction.atomic
def promote_guest_session(session: GuestSession, validated_data: dict) -> dict:
    session = GuestSession.objects.select_for_update().get(pk=session.pk)
    if session.expire_if_needed() or not session.is_usable:
        raise DjangoValidationError({"guest_session": "Guest session is not active."})

    ai_session = _latest_guest_ai_session(session)
    if ai_session is not None:
        ai_session = AiSession.objects.select_for_update().get(pk=ai_session.pk)
    snapshot = _diagnostic_snapshot_for(ai_session)
    latest_message = _latest_user_message(ai_session)
    category = _resolve_promotion_category(validated_data, snapshot)
    if category is None:
        raise DjangoValidationError(
            {"category_id": "A category is required to create a case from this guest session."}
        )

    user = User.objects.create_user(
        email=validated_data["email"],
        password=validated_data["password"],
        first_name=validated_data.get("first_name", "").strip(),
        last_name=validated_data.get("last_name", "").strip(),
    )
    organization = get_or_create_personal_organization(user)
    case = Case.objects.create(
        customer_user=user,
        owner_organization=organization,
        category=category,
        title=_build_promoted_case_title(validated_data, snapshot, category),
        description=_build_promoted_case_description(validated_data, snapshot, latest_message),
        status=Case.Statuses.IN_DIAGNOSIS if ai_session is not None else Case.Statuses.OPEN,
        priority=_build_promoted_case_priority(snapshot),
        source=Case.Sources.TROUBLESHOOTING,
    )

    create_case_event(
        case=case,
        event_type=CaseEvent.EventTypes.CASE_CREATED,
        actor_user=user,
        payload={
            "source": "guest_promotion",
            "guest_session_id": str(session.public_id),
            "ai_session_id": ai_session.id if ai_session is not None else None,
            "diagnostic_snapshot_id": snapshot.id if snapshot is not None else None,
        },
    )

    if ai_session is not None:
        ai_session.user = user
        ai_session.case = case
        ai_session.guest_session = None
        ai_session.save(update_fields=["user", "case", "guest_session", "updated_at"])
        AiUsageLedger.objects.filter(session=ai_session, guest_session=session).update(
            user=user,
            guest_session=None,
            organization=organization,
            case=case,
        )

    if snapshot is not None:
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.AI_DIAGNOSTIC_PROGRESS,
            actor_user=user,
            payload={
                "source": "guest_promotion",
                "ai_session_id": ai_session.id if ai_session is not None else None,
                "diagnostic_snapshot_id": snapshot.id,
                "risk_level": snapshot.risk_level,
                "escalation_recommended": snapshot.escalation_recommended,
            },
        )

    metadata = dict(session.metadata_json or {})
    metadata["promotion"] = {
        "user_id": user.id,
        "case_id": case.id,
        "ai_session_id": ai_session.id if ai_session is not None else None,
    }
    session.status = GuestSession.Statuses.PROMOTED
    session.promoted_to_user = user
    session.promoted_at = timezone.now()
    session.metadata_json = metadata
    session.save(update_fields=["status", "promoted_to_user", "promoted_at", "metadata_json", "updated_at"])

    return {
        "guest_session": session,
        "user": user,
        "case": case,
        "ai_session": ai_session,
        "diagnostic_snapshot": snapshot,
    }
