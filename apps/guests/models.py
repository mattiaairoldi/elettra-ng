import uuid

from django.db import models
from django.utils import timezone


class GuestSession(models.Model):
    class Statuses(models.TextChoices):
        ACTIVE = "active", "Active"
        PROMOTED = "promoted", "Promoted"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, choices=Statuses.choices, default=Statuses.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    promoted_to_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promoted_guest_sessions",
    )
    promoted_at = models.DateTimeField(null=True, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("public_id", "status"), name="guest_public_status_idx"),
            models.Index(fields=("ip_hash", "created_at"), name="guest_ip_created_idx"),
            models.Index(fields=("status", "expires_at"), name="guest_status_expiry_idx"),
        ]

    def __str__(self):
        return f"Guest {self.public_id}"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    @property
    def is_usable(self) -> bool:
        return self.status == self.Statuses.ACTIVE and not self.is_expired

    def expire_if_needed(self) -> bool:
        if self.status == self.Statuses.ACTIVE and self.is_expired:
            self.status = self.Statuses.EXPIRED
            self.save(update_fields=["status", "updated_at"])
            return True
        return False
