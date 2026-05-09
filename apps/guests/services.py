import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, Throttled

from .models import GuestSession


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
