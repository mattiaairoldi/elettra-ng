from django.contrib import admin

from .models import Organization, OrganizationInvitation, OrganizationMembership, OrganizationPlan


@admin.register(OrganizationPlan)
class OrganizationPlanAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "kind", "max_members", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("slug", "name")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "plan", "status", "personal_owner")
    list_filter = ("kind", "status", "plan")
    search_fields = ("name", "personal_owner__email")
    autocomplete_fields = ("plan", "personal_owner", "created_by_user")


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("organization", "user", "role", "scope", "status")
    list_filter = ("role", "scope", "status")
    search_fields = ("organization__name", "user__email")
    autocomplete_fields = ("organization", "user", "approved_by_user")


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ("organization", "email", "role", "scope", "status", "expires_at")
    list_filter = ("status", "role", "scope")
    search_fields = ("organization__name", "email", "invited_by_user__email")
    autocomplete_fields = (
        "organization",
        "invited_by_user",
        "accepted_by_user",
        "accepted_membership",
        "revoked_by_user",
    )
