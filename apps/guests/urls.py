from django.urls import path

from .views import (
    GuestDiagnosticSnapshotView,
    GuestDiagnosticTurnView,
    GuestMessageDetailView,
    GuestPromotionView,
    GuestSessionCreateView,
    GuestSessionCurrentView,
)


app_name = "guests"

urlpatterns = [
    path("guest/sessions", GuestSessionCreateView.as_view(), name="guest-session-create"),
    path("guest/sessions/current", GuestSessionCurrentView.as_view(), name="guest-session-current"),
    path("guest/promote", GuestPromotionView.as_view(), name="guest-promote"),
    path("guest/diagnostic-turns", GuestDiagnosticTurnView.as_view(), name="guest-diagnostic-turns"),
    path("guest/messages/<int:message_id>", GuestMessageDetailView.as_view(), name="guest-message-detail"),
    path("guest/diagnostic-snapshot", GuestDiagnosticSnapshotView.as_view(), name="guest-diagnostic-snapshot"),
]
