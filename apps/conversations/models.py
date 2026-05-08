from django.db import models


class Conversation(models.Model):
    class Statuses(models.TextChoices):
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    subject = models.CharField(max_length=200)
    case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    case_share_request = models.OneToOneField(
        "cases.CaseShareRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation",
    )
    created_by_user = models.ForeignKey("identity.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_conversations")
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.ACTIVE)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at", "-id")
        indexes = [
            models.Index(fields=("status", "updated_at"), name="conv_status_updated_idx"),
        ]

    def __str__(self):
        return self.subject


class ConversationParticipant(models.Model):
    class Statuses(models.TextChoices):
        ACTIVE = "active", "Active"
        REMOVED = "removed", "Removed"

    class Roles(models.TextChoices):
        OWNER = "owner", "Owner"
        PARTICIPANT = "participant", "Participant"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="conversation_participants")
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversation_participants",
    )
    membership = models.ForeignKey(
        "organizations.OrganizationMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation_participants",
    )
    role = models.CharField(max_length=32, choices=Roles.choices, default=Roles.PARTICIPANT)
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("conversation_id", "id")
        constraints = [
            models.UniqueConstraint(fields=("conversation", "user", "organization"), name="unique_conversation_user_org"),
        ]
        indexes = [
            models.Index(fields=("user", "status"), name="conv_part_user_status_idx"),
            models.Index(fields=("organization", "status"), name="conv_part_org_status_idx"),
            models.Index(fields=("conversation", "status"), name="conv_part_conv_status_idx"),
        ]

    def __str__(self):
        return f"{self.user} in {self.conversation}"


class ConversationPost(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="posts")
    author_user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="conversation_posts")
    author_membership = models.ForeignKey(
        "organizations.OrganizationMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation_posts",
    )
    body = models.TextField()
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=("conversation", "created_at"), name="conv_post_conv_created_idx"),
        ]

    def __str__(self):
        return f"Post {self.pk} in {self.conversation}"
