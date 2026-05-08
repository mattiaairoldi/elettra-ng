from rest_framework.routers import DefaultRouter

from .views import AiSessionViewSet


app_name = "ai_assistant"

router = DefaultRouter(trailing_slash=False)
router.register("ai/sessions", AiSessionViewSet, basename="ai-session")

urlpatterns = router.urls
