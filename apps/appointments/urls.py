from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet


app_name = "appointments"

router = DefaultRouter(trailing_slash=False)
router.register("appointments", AppointmentViewSet, basename="appointment")

urlpatterns = router.urls
