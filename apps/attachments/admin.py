from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("file_name", "attachment_type", "uploaded_by_user", "case", "asset", "created_at")
    list_filter = ("attachment_type",)
    search_fields = ("file_name", "uploaded_by_user__email")
