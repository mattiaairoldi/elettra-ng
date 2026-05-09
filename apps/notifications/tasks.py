from celery import shared_task

from .models import DeviceInstallation, Notification


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def deliver_notification_pushes_task(notification_id):
    notification = Notification.objects.filter(id=notification_id).first()
    if notification is None:
        return {"status": "missing"}

    active_installations = DeviceInstallation.objects.filter(
        user=notification.recipient_user,
        is_active=True,
    ).exclude(push_provider=DeviceInstallation.PushProviders.NONE)
    return {"status": "provider_not_configured", "installation_count": active_installations.count()}
