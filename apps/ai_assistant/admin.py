from django.contrib import admin

from .models import AiDiagnosticSnapshot, AiMessage, AiSession


@admin.register(AiSession)
class AiSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "case", "status", "started_at", "ended_at")
    list_filter = ("status",)
    search_fields = ("user__email", "case__title")
    readonly_fields = ("user", "case", "status", "started_at", "ended_at", "created_at", "updated_at")


@admin.register(AiMessage)
class AiMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "status", "created_at", "short_error_detail")
    list_filter = ("role", "status")
    search_fields = ("session__user__email", "content")
    readonly_fields = ("session", "role", "content", "status", "error_detail", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Error")
    def short_error_detail(self, obj):
        return (obj.error_detail or "")[:80]


@admin.register(AiDiagnosticSnapshot)
class AiDiagnosticSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "risk_level", "escalation_recommended", "updated_at")
    list_filter = ("risk_level", "escalation_recommended")
    search_fields = ("session__user__email", "session__case__title", "summary", "next_question")
    readonly_fields = (
        "session",
        "source_message",
        "summary",
        "risk_level",
        "next_question",
        "escalation_recommended",
        "escalation_reason",
        "recommendation",
        "facts_json",
        "safety_notes_json",
        "raw_payload_json",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
