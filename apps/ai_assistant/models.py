from django.db import models
from django.utils import timezone


class AiSession(models.Model):
    class Statuses(models.TextChoices):
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"

    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_sessions")
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="ai_sessions")
    status = models.CharField(max_length=16, choices=Statuses.choices, default=Statuses.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-started_at", "-id")


class AiMessage(models.Model):
    class Roles(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    class Statuses(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    session = models.ForeignKey(AiSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Roles.choices)
    content = models.TextField()
    status = models.CharField(max_length=16, choices=Statuses.choices, default=Statuses.COMPLETED)
    error_detail = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class AiDiagnosticSnapshot(models.Model):
    class RiskLevels(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    session = models.OneToOneField(AiSession, on_delete=models.CASCADE, related_name="diagnostic_snapshot")
    diagnostic_chapter = models.ForeignKey(
        "troubleshooting.DiagnosticChapter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_diagnostic_snapshots",
    )
    diagnostic_chapter_option = models.ForeignKey(
        "troubleshooting.DiagnosticChapterOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_diagnostic_snapshots",
    )
    source_message = models.ForeignKey(
        AiMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diagnostic_snapshots",
    )
    summary = models.TextField(blank=True)
    risk_level = models.CharField(max_length=16, choices=RiskLevels.choices, default=RiskLevels.UNKNOWN)
    next_question = models.TextField(blank=True)
    escalation_recommended = models.BooleanField(default=False)
    escalation_reason = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    facts_json = models.JSONField(default=dict, blank=True)
    excluded_facts_json = models.JSONField(default=dict, blank=True)
    asked_questions_json = models.JSONField(default=list, blank=True)
    safety_notes_json = models.JSONField(default=list, blank=True)
    compacted_summary = models.TextField(blank=True)
    context_version = models.PositiveIntegerField(default=1)
    context_metadata_json = models.JSONField(default=dict, blank=True)
    raw_payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-id")


class AiContextDigest(models.Model):
    class RiskLevels(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    session = models.ForeignKey(AiSession, on_delete=models.CASCADE, related_name="context_digests")
    from_message = models.ForeignKey(
        AiMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="context_digests_from",
    )
    to_message = models.ForeignKey(
        AiMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="context_digests_to",
    )
    source_snapshot = models.ForeignKey(
        AiDiagnosticSnapshot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="context_digests",
    )
    summary = models.TextField(blank=True)
    risk_level = models.CharField(max_length=16, choices=RiskLevels.choices, default=RiskLevels.UNKNOWN)
    facts_json = models.JSONField(default=dict, blank=True)
    excluded_facts_json = models.JSONField(default=dict, blank=True)
    asked_questions_json = models.JSONField(default=list, blank=True)
    safety_notes_json = models.JSONField(default=list, blank=True)
    message_count = models.PositiveIntegerField(default=0)
    total_completed_messages = models.PositiveIntegerField(default=0)
    estimated_input_tokens = models.PositiveIntegerField(default=0)
    estimated_output_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    provider = models.CharField(max_length=64, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    trigger_reason = models.CharField(max_length=64, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")


class AiUsageLedger(models.Model):
    class Purposes(models.TextChoices):
        CHAT = "chat", "Chat"
        DIAGNOSTIC = "diagnostic", "Diagnostic"
        CONTEXT_COMPACTION = "context_compaction", "Context compaction"

    session = models.ForeignKey(AiSession, on_delete=models.CASCADE, related_name="usage_ledger")
    message = models.ForeignKey(
        AiMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_ledger",
    )
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="ai_usage_ledger")
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_usage_ledger",
    )
    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_usage_ledger",
    )
    purpose = models.CharField(max_length=32, choices=Purposes.choices)
    provider = models.CharField(max_length=64, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("user", "created_at"), name="ai_usage_user_created_idx"),
            models.Index(fields=("organization", "created_at"), name="ai_usage_org_created_idx"),
            models.Index(fields=("case", "purpose"), name="ai_usage_case_purpose_idx"),
        ]
