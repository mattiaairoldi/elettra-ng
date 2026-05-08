from django.contrib import admin

from .models import (
    DiagnosticChapter,
    DiagnosticChapterOption,
    DiagnosticFlow,
    DiagnosticNode,
    DiagnosticOption,
    DiagnosticSafetyRule,
)


class DiagnosticChapterOptionInline(admin.TabularInline):
    model = DiagnosticChapterOption
    extra = 0
    fields = ("label", "slug", "option_type", "sort_order", "is_active")
    prepopulated_fields = {"slug": ("label",)}


class DiagnosticSafetyRuleInline(admin.TabularInline):
    model = DiagnosticSafetyRule
    extra = 0
    fields = ("title", "risk_level", "escalation_level", "sort_order", "is_active")


@admin.register(DiagnosticChapter)
class DiagnosticChapterAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "category", "status", "is_public", "sort_order")
    list_filter = ("status", "is_public", "category")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (DiagnosticChapterOptionInline, DiagnosticSafetyRuleInline)


@admin.register(DiagnosticChapterOption)
class DiagnosticChapterOptionAdmin(admin.ModelAdmin):
    list_display = ("label", "chapter", "option_type", "sort_order", "is_active")
    list_filter = ("option_type", "is_active", "chapter")
    search_fields = ("label", "slug", "chapter__name")
    readonly_fields = ("created_at", "updated_at")
    prepopulated_fields = {"slug": ("label",)}


@admin.register(DiagnosticSafetyRule)
class DiagnosticSafetyRuleAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "risk_level", "escalation_level", "sort_order", "is_active")
    list_filter = ("risk_level", "escalation_level", "is_active", "chapter")
    search_fields = ("title", "chapter__name", "guidance")
    readonly_fields = ("created_at", "updated_at")


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
