from django.contrib import admin

from .models import ProfessionalProfile


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "is_available", "service_area_text")
    list_filter = ("is_available", "categories", "tags")
    search_fields = ("display_name", "user__email", "bio", "service_area_text")
    filter_horizontal = ("categories", "tags")
