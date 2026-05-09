from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health_view(_request):
    return JsonResponse({"status": "ok"})


api_v1_patterns = [
    path("health", health_view, name="health"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api_v1:schema"), name="docs"),
    path("auth/", include(("apps.identity.urls", "identity"), namespace="auth")),
    path("", include(("apps.organizations.urls", "organizations"), namespace="organizations")),
    path("", include(("apps.taxonomy.urls", "taxonomy"), namespace="taxonomy")),
    path("", include(("apps.troubleshooting.urls", "troubleshooting"), namespace="troubleshooting")),
    path("", include(("apps.cases.urls", "cases"), namespace="cases")),
    path("", include(("apps.conversations.urls", "conversations"), namespace="conversations")),
    path("", include(("apps.professionals.urls", "professionals"), namespace="professionals")),
    path("", include(("apps.appointments.urls", "appointments"), namespace="appointments")),
    path("", include(("apps.attachments.urls", "attachments"), namespace="attachments")),
    path("", include(("apps.guests.urls", "guests"), namespace="guests")),
    path("", include(("apps.notifications.urls", "notifications"), namespace="notifications")),
    path("", include(("apps.ai_assistant.urls", "ai_assistant"), namespace="ai_assistant")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "api_v1"))),
]
