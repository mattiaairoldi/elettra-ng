from django.contrib import admin

from .models import DiagnosticFlow, DiagnosticNode, DiagnosticOption


@admin.register(DiagnosticFlow)
class DiagnosticFlowAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "version", "is_public")
    list_filter = ("status", "is_public", "category")
    search_fields = ("title", "slug")
    readonly_fields = ("version", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(DiagnosticNode)
class DiagnosticNodeAdmin(admin.ModelAdmin):
    list_display = ("title", "flow", "node_type", "sort_order", "is_entrypoint", "created_at")
    list_filter = ("node_type", "is_entrypoint", "flow")
    search_fields = ("title", "flow__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DiagnosticOption)
class DiagnosticOptionAdmin(admin.ModelAdmin):
    list_display = ("label", "from_node", "to_node", "sort_order", "is_default")
    list_filter = ("is_default", "from_node__flow")
    search_fields = ("label", "from_node__title", "to_node__title")
    readonly_fields = ("metadata_json",)
