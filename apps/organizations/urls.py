from rest_framework.routers import DefaultRouter

from .views import OrganizationMembershipViewSet, OrganizationViewSet


app_name = "organizations"

router = DefaultRouter(trailing_slash=False)
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("organization-memberships", OrganizationMembershipViewSet, basename="organization-membership")

urlpatterns = router.urls

