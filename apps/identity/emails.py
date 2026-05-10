from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .tokens import generate_email_verification_token, generate_password_reset_token


def build_absolute_path(path: str) -> str:
    base_url = settings.APP_BASE_URL.rstrip("/")
    return f"{base_url}{path}"


def build_web_url(path: str) -> str:
    base_url = settings.WEB_APP_BASE_URL.rstrip("/")
    return f"{base_url}{path}"


def send_verification_email(user) -> None:
    token = generate_email_verification_token(user.email)
    verify_url = build_web_url(f"/#/verify-email?token={token}")
    send_mail(
        subject="Conferma la tua email Elettra",
        message=(
            "Conferma la tua email per attivare l'account Elettra.\n\n"
            f"{verify_url}\n\n"
            "Se il link non si apre, copia l'indirizzo nel browser."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_password_reset_email(user) -> None:
    token = generate_password_reset_token(user.email)
    reset_path = reverse("api_v1:auth:reset-password")
    reset_url = build_absolute_path(reset_path)
    send_mail(
        subject="Reset your password",
        message=(
            "Use this token to reset your password:\n\n"
            f"{token}\n\n"
            "Reset endpoint:\n"
            f"{reset_url}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
