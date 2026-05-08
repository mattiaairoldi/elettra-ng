from django.db import models


def attachment_upload_to(_instance, filename):
    return f"attachments/{filename}"


class Attachment(models.Model):
    class AttachmentTypes(models.TextChoices):
        IMAGE = "image", "Image"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    uploaded_by_user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="attachments")
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")
    asset = models.ForeignKey("cases.Asset", on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")
    file = models.FileField(upload_to=attachment_upload_to)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    attachment_type = models.CharField(max_length=32, choices=AttachmentTypes.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
