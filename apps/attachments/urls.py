from rest_framework.routers import DefaultRouter

from .views import AttachmentViewSet


app_name = "attachments"

router = DefaultRouter(trailing_slash=False)
router.register("attachments", AttachmentViewSet, basename="attachment")

urlpatterns = router.urls
