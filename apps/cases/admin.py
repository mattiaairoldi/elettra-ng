from django.contrib import admin

from .models import Asset, Case, CaseEvent, CaseNote, CaseShareRequest, Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_user", "organization", "city")
    search_fields = ("name", "city", "owner_user__email", "organization__name")
    autocomplete_fields = ("owner_user", "organization")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "property", "category", "location_text")
    list_filter = ("category",)
    search_fields = ("name", "property__name")


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "customer_user",
        "owner_organization",
        "assigned_professional",
        "category",
        "status",
        "priority",
        "source",
    )
    list_filter = ("status", "priority", "source", "category")
    search_fields = ("title", "customer_user__email", "owner_organization__name", "assigned_professional__email")
    autocomplete_fields = ("customer_user", "owner_organization", "assigned_professional", "category", "property", "asset")


@admin.register(CaseEvent)
class CaseEventAdmin(admin.ModelAdmin):
    list_display = ("case", "event_type", "actor_user", "created_at")
    list_filter = ("event_type",)
    search_fields = ("case__title", "actor_user__email")
    readonly_fields = ("case", "event_type", "actor_user", "payload_json", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ("case", "author_user", "note_type", "is_internal", "created_at")
    list_filter = ("note_type", "is_internal")


@admin.register(CaseShareRequest)
class CaseShareRequestAdmin(admin.ModelAdmin):
    list_display = ("case", "recipient_organization", "recipient_membership", "status", "share_scope", "created_at")
    list_filter = ("status", "share_scope", "recipient_organization")
    search_fields = ("case__title", "requester_user__email", "recipient_organization__name")
    autocomplete_fields = (
        "case",
        "requester_user",
        "recipient_organization",
        "recipient_membership",
        "accepted_by_user",
        "rejected_by_user",
        "revoked_by_user",
    )
