from django.contrib import admin

from .models import Conversation, ConversationParticipant, ConversationPost


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    autocomplete_fields = ("user", "organization", "membership")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("subject", "case", "status", "created_by_user", "updated_at")
    list_filter = ("status",)
    search_fields = ("subject", "case__title", "created_by_user__email")
    autocomplete_fields = ("case", "case_share_request", "created_by_user")
    inlines = (ConversationParticipantInline,)


@admin.register(ConversationPost)
class ConversationPostAdmin(admin.ModelAdmin):
    list_display = ("conversation", "author_user", "created_at")
    search_fields = ("conversation__subject", "author_user__email", "body")
    autocomplete_fields = ("conversation", "author_user", "author_membership")

