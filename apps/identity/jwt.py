from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


def _seconds(value) -> int:
    return int(value.total_seconds())


def build_token_payload(user) -> dict:
    refresh = RefreshToken.for_user(user)
    simple_jwt_settings = settings.SIMPLE_JWT
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "token_type": "Bearer",
        "access_expires_in": _seconds(simple_jwt_settings["ACCESS_TOKEN_LIFETIME"]),
        "refresh_expires_in": _seconds(simple_jwt_settings["REFRESH_TOKEN_LIFETIME"]),
    }


def build_refresh_payload(validated_data: dict) -> dict:
    simple_jwt_settings = settings.SIMPLE_JWT
    payload = {
        "access": validated_data["access"],
        "token_type": "Bearer",
        "access_expires_in": _seconds(simple_jwt_settings["ACCESS_TOKEN_LIFETIME"]),
    }
    if "refresh" in validated_data:
        payload["refresh"] = validated_data["refresh"]
        payload["refresh_expires_in"] = _seconds(simple_jwt_settings["REFRESH_TOKEN_LIFETIME"])
    return payload


def record_token_login(user) -> None:
    now = timezone.now()
    user.last_login = now
    user.last_login_at = now
    user.updated_at = now
    user.save(update_fields=["last_login", "last_login_at", "updated_at"])
