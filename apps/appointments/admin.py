from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("case", "professional_profile", "scheduled_start_at", "status")
    list_filter = ("status",)
    search_fields = ("case__title", "professional_profile__display_name")
