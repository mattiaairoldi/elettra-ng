from django.contrib.gis.db import models
from django.utils import timezone


class Property(models.Model):
    owner_user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="properties")
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="properties")
    name = models.CharField(max_length=200)
    address_text = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    location = models.PointField(srid=4326, geography=True, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.owner_user_id and not self.organization_id:
            from apps.organizations.services import get_or_create_personal_organization

            self.organization = get_or_create_personal_organization(self.owner_user)
        super().save(*args, **kwargs)


class Asset(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="assets")
    category = models.ForeignKey("taxonomy.Category", on_delete=models.PROTECT, related_name="assets")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location_text = models.CharField(max_length=200, blank=True)
    location = models.PointField(srid=4326, geography=True, null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")

    def __str__(self):
        return self.name


class Case(models.Model):
    class Statuses(models.TextChoices):
        OPEN = "open", "Open"
        IN_DIAGNOSIS = "in_diagnosis", "In diagnosis"
        WAITING_PROFESSIONAL = "waiting_professional", "Waiting professional"
        SCHEDULED = "scheduled", "Scheduled"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    class Priorities(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Sources(models.TextChoices):
        MANUAL = "manual", "Manual"
        TROUBLESHOOTING = "troubleshooting", "Troubleshooting"
        PROFESSIONAL = "professional", "Professional"

    customer_user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="cases")
    owner_organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="cases")
    assigned_professional = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
    )
    category = models.ForeignKey("taxonomy.Category", on_delete=models.PROTECT, related_name="cases")
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name="cases")
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="cases")
    troubleshooting_flow = models.ForeignKey(
        "troubleshooting.DiagnosticFlow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cases",
    )
    current_diagnostic_node = models.ForeignKey(
        "troubleshooting.DiagnosticNode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_cases",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.OPEN)
    priority = models.CharField(max_length=16, choices=Priorities.choices, default=Priorities.NORMAL)
    source = models.CharField(max_length=32, choices=Sources.choices, default=Sources.MANUAL)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.owner_organization_id:
            if self.property_id:
                self.owner_organization = self.property.organization
            elif self.customer_user_id:
                from apps.organizations.services import get_or_create_personal_organization

                self.owner_organization = get_or_create_personal_organization(self.customer_user)
        super().save(*args, **kwargs)


class CaseShareRequest(models.Model):
    class Statuses(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        REVOKED = "revoked", "Revoked"

    class ShareScopes(models.TextChoices):
        SUMMARY = "summary", "Summary"
        DIAGNOSTIC_CHAT = "diagnostic_chat", "Diagnostic chat"
        SELECTED_ATTACHMENTS = "selected_attachments", "Selected attachments"
        FULL_CASE = "full_case", "Full case"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="share_requests")
    requester_user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="case_share_requests")
    recipient_organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="received_case_share_requests",
    )
    recipient_membership = models.ForeignKey(
        "organizations.OrganizationMembership",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="received_case_share_requests",
    )
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.PENDING)
    share_scope = models.CharField(max_length=32, choices=ShareScopes.choices, default=ShareScopes.SUMMARY)
    visible_title = models.CharField(max_length=200)
    visible_summary = models.TextField(blank=True)
    shared_payload_json = models.JSONField(default=dict, blank=True)
    rejection_reason = models.TextField(blank=True)
    accepted_by_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_case_share_requests",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_by_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_case_share_requests",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    revoked_by_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_case_share_requests",
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("case", "status"), name="case_share_case_status_idx"),
            models.Index(fields=("recipient_organization", "status"), name="case_share_org_status_idx"),
            models.Index(fields=("recipient_membership", "status"), name="case_share_member_status_idx"),
        ]

    def __str__(self):
        return f"{self.case} -> {self.recipient_organization}"


class CaseEvent(models.Model):
    class EventTypes(models.TextChoices):
        CASE_CREATED = "case_created", "Case created"
        STATUS_CHANGED = "status_changed", "Status changed"
        PROFESSIONAL_ASSIGNED = "professional_assigned", "Professional assigned"
        TROUBLESHOOTING_STARTED = "troubleshooting_started", "Troubleshooting started"
        TROUBLESHOOTING_PROGRESS = "troubleshooting_progress", "Troubleshooting progress"
        AI_DIAGNOSTIC_PROGRESS = "ai_diagnostic_progress", "AI diagnostic progress"
        NOTE_ADDED = "note_added", "Note added"
        APPOINTMENT_CREATED = "appointment_created", "Appointment created"
        APPOINTMENT_STATUS_CHANGED = "appointment_status_changed", "Appointment status changed"
        CASE_SHARE_REQUEST_CREATED = "case_share_request_created", "Case share request created"
        CASE_SHARE_REQUEST_ACCEPTED = "case_share_request_accepted", "Case share request accepted"
        CASE_SHARE_REQUEST_REJECTED = "case_share_request_rejected", "Case share request rejected"
        CASE_SHARE_REQUEST_REVOKED = "case_share_request_revoked", "Case share request revoked"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=64, choices=EventTypes.choices)
    actor_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case_events",
    )
    payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class CaseNote(models.Model):
    class NoteTypes(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        PROFESSIONAL = "professional", "Professional"
        OPERATOR = "operator", "Operator"
        SYSTEM = "system", "System"

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="notes")
    author_user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="case_notes")
    note_type = models.CharField(max_length=32, choices=NoteTypes.choices)
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "id")
