from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, CaseViewSet, PropertyViewSet


app_name = "cases"

router = DefaultRouter(trailing_slash=False)
router.register("properties", PropertyViewSet, basename="property")
router.register("assets", AssetViewSet, basename="asset")
router.register("cases", CaseViewSet, basename="case")

urlpatterns = router.urls
