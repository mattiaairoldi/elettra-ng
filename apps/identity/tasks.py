from celery import shared_task

from .emails import send_password_reset_email, send_verification_email
from .models import User


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_verification_email_task(user_id):
    user = User.objects.get(id=user_id, is_active=True)
    send_verification_email(user)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_password_reset_email_task(user_id):
    user = User.objects.get(id=user_id, is_active=True)
    send_password_reset_email(user)
