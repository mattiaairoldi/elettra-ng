from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .tokens import generate_organization_invitation_token


def build_absolute_path(path: str) -> str:
    base_url = settings.APP_BASE_URL.rstrip("/")
    return f"{base_url}{path}"


def send_organization_invitation_email(invitation) -> None:
    token = generate_organization_invitation_token(invitation)
    accept_path = reverse("api_v1:organizations:organization-invitation-accept")
    accept_url = build_absolute_path(accept_path)
    send_mail(
        subject=f"Invitation to join {invitation.organization.name}",
        message=(
            f"You have been invited to join {invitation.organization.name}.\n\n"
            "Use this token to accept the invitation:\n\n"
            f"{token}\n\n"
            "Accept endpoint:\n"
            f"{accept_url}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        fail_silently=False,
    )

