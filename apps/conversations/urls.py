from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet


app_name = "conversations"

router = DefaultRouter(trailing_slash=False)
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = router.urls

