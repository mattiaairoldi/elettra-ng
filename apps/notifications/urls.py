from rest_framework.routers import DefaultRouter

from .views import DeviceInstallationViewSet, NotificationViewSet


app_name = "notifications"

router = DefaultRouter(trailing_slash=False)
router.register("notifications", NotificationViewSet, basename="notification")
router.register("device-installations", DeviceInstallationViewSet, basename="device-installation")

urlpatterns = router.urls
