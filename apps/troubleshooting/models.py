from django.core.exceptions import ValidationError
from django.db import models


class DiagnosticChapter(models.Model):
    class Statuses(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        "taxonomy.Category",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="diagnostic_chapters",
    )
    prompt_context = models.TextField(blank=True)
    safety_context = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.DRAFT)
    is_public = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name", "id")

    def __str__(self):
        return self.name


class DiagnosticChapterOption(models.Model):
    class OptionTypes(models.TextChoices):
        ASSET_TYPE = "asset_type", "Asset type"
        SYMPTOM = "symptom", "Symptom"
        SAFETY_SIGNAL = "safety_signal", "Safety signal"
        GENERIC = "generic", "Generic"

    chapter = models.ForeignKey(DiagnosticChapter, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=160)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    option_type = models.CharField(max_length=32, choices=OptionTypes.choices, default=OptionTypes.GENERIC)
    prompt_hint = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "label", "id")
        constraints = [
            models.UniqueConstraint(fields=("chapter", "slug"), name="unique_diagnostic_chapter_option_slug"),
        ]

    def __str__(self):
        return self.label


class DiagnosticSafetyRule(models.Model):
    class EscalationLevels(models.TextChoices):
        NONE = "none", "None"
        RECOMMENDED = "recommended", "Recommended"
        REQUIRED = "required", "Required"
        URGENT = "urgent", "Urgent"

    class RiskLevels(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    chapter = models.ForeignKey(DiagnosticChapter, on_delete=models.CASCADE, related_name="safety_rules")
    title = models.CharField(max_length=160)
    trigger_terms_json = models.JSONField(default=list, blank=True)
    guidance = models.TextField(blank=True)
    risk_level = models.CharField(max_length=16, choices=RiskLevels.choices, default=RiskLevels.UNKNOWN)
    escalation_level = models.CharField(
        max_length=16,
        choices=EscalationLevels.choices,
        default=EscalationLevels.NONE,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "title", "id")

    def __str__(self):
        return self.title


class DiagnosticFlow(models.Model):
    class Statuses(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey("taxonomy.Category", on_delete=models.PROTECT, related_name="diagnostic_flows")
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.DRAFT)
    version = models.PositiveIntegerField(default=1)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title


class DiagnosticNode(models.Model):
    class NodeTypes(models.TextChoices):
        QUESTION = "question", "Question"
        SOLUTION = "solution", "Solution"
        WARNING = "warning", "Warning"
        ESCALATION = "escalation", "Escalation"

    flow = models.ForeignKey(DiagnosticFlow, on_delete=models.CASCADE, related_name="nodes")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    node_type = models.CharField(max_length=32, choices=NodeTypes.choices)
    sort_order = models.PositiveIntegerField(default=0)
    is_entrypoint = models.BooleanField(default=False)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.is_entrypoint:
            queryset = DiagnosticNode.objects.filter(flow=self.flow, is_entrypoint=True)
            if self.pk is not None:
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                raise ValidationError({"is_entrypoint": "Only one entrypoint node is allowed per flow."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class DiagnosticOption(models.Model):
    from_node = models.ForeignKey(DiagnosticNode, on_delete=models.CASCADE, related_name="options")
    to_node = models.ForeignKey(
        DiagnosticNode,
        on_delete=models.CASCADE,
        related_name="incoming_options",
        null=True,
        blank=True,
    )
    label = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.label

    def clean(self):
        super().clean()
        if self.to_node_id is not None and self.from_node_id is not None and self.to_node.flow_id != self.from_node.flow_id:
            raise ValidationError({"to_node": "Option target node must belong to the same flow."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
