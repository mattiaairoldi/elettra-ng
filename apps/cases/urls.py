from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, CaseShareRequestViewSet, CaseViewSet, PropertyViewSet


app_name = "cases"

router = DefaultRouter(trailing_slash=False)
router.register("properties", PropertyViewSet, basename="property")
router.register("assets", AssetViewSet, basename="asset")
router.register("cases", CaseViewSet, basename="case")
router.register("case-share-requests", CaseShareRequestViewSet, basename="case-share-request")

urlpatterns = router.urls
