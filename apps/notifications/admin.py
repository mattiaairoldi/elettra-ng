from django.contrib import admin

from .models import DeviceInstallation, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient_user", "notification_type", "priority", "read_at", "created_at")
    list_filter = ("notification_type", "priority", "read_at")
    search_fields = ("title", "body", "recipient_user__email", "actor_user__email")
    autocomplete_fields = ("recipient_user", "actor_user")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DeviceInstallation)
class DeviceInstallationAdmin(admin.ModelAdmin):
    list_display = ("installation_id", "user", "platform", "push_provider", "is_active", "last_seen_at")
    list_filter = ("platform", "push_provider", "is_active")
    search_fields = ("installation_id", "user__email", "device_model", "app_version")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at", "last_seen_at", "deactivated_at")
