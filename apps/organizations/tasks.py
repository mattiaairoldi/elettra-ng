from celery import shared_task

from .emails import send_organization_invitation_email
from .models import OrganizationInvitation


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_organization_invitation_email_task(invitation_id):
    invitation = OrganizationInvitation.objects.select_related("organization").filter(
        id=invitation_id,
        status=OrganizationInvitation.Statuses.PENDING,
    ).first()
    if invitation is None:
        return
    send_organization_invitation_email(invitation)
