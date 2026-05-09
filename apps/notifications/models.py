import uuid

from django.db import models
from django.utils import timezone as django_timezone


class Notification(models.Model):
    class Types(models.TextChoices):
        CASE_SHARE_REQUEST_CREATED = "case_share_request_created", "Case share request created"
        CASE_SHARE_REQUEST_ACCEPTED = "case_share_request_accepted", "Case share request accepted"
        CASE_SHARE_REQUEST_REJECTED = "case_share_request_rejected", "Case share request rejected"
        CASE_SHARE_REQUEST_REVOKED = "case_share_request_revoked", "Case share request revoked"
        CONVERSATION_POST_CREATED = "conversation_post_created", "Conversation post created"
        APPOINTMENT_CREATED = "appointment_created", "Appointment created"
        APPOINTMENT_STATUS_CHANGED = "appointment_status_changed", "Appointment status changed"
        MAINTENANCE_REMINDER_DUE = "maintenance_reminder_due", "Maintenance reminder due"
        SYSTEM = "system", "System"

    class Priorities(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    recipient_user = models.ForeignKey(
        "identity.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )
    notification_type = models.CharField(max_length=64, choices=Types.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    priority = models.CharField(max_length=16, choices=Priorities.choices, default=Priorities.NORMAL)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    deep_link = models.CharField(max_length=255, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("recipient_user", "read_at", "created_at"), name="notif_rec_read_created_idx"),
            models.Index(fields=("recipient_user", "notification_type"), name="notif_rec_type_idx"),
            models.Index(fields=("target_type", "target_id"), name="notif_target_idx"),
        ]

    def __str__(self):
        return self.title

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_read(self, *, when=None):
        if self.read_at is not None:
            return False
        self.read_at = when or django_timezone.now()
        self.save(update_fields=["read_at", "updated_at"])
        return True


class DeviceInstallation(models.Model):
    class Platforms(models.TextChoices):
        IOS = "ios", "iOS"
        ANDROID = "android", "Android"
        WEB = "web", "Web"
        UNKNOWN = "unknown", "Unknown"

    class PushProviders(models.TextChoices):
        FCM = "fcm", "Firebase Cloud Messaging"
        APNS = "apns", "Apple Push Notification service"
        WEB_PUSH = "web_push", "Web Push"
        NONE = "none", "None"

    installation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        "identity.User",
        on_delete=models.CASCADE,
        related_name="device_installations",
    )
    platform = models.CharField(max_length=32, choices=Platforms.choices, default=Platforms.UNKNOWN)
    push_provider = models.CharField(max_length=32, choices=PushProviders.choices, default=PushProviders.NONE)
    push_token = models.CharField(max_length=512, blank=True)
    app_version = models.CharField(max_length=64, blank=True)
    device_model = models.CharField(max_length=120, blank=True)
    locale = models.CharField(max_length=32, blank=True)
    timezone = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(default=django_timezone.now)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_seen_at", "-id")
        indexes = [
            models.Index(fields=("user", "is_active", "last_seen_at"), name="device_user_active_seen_idx"),
            models.Index(fields=("push_provider", "is_active"), name="device_provider_active_idx"),
        ]

    def __str__(self):
        return f"{self.user} {self.platform} {self.installation_id}"
