from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from apps.common.serializers import GeoPointField
from apps.organizations.models import Organization, OrganizationMembership

from .models import ProfessionalProfile


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    category_ids = serializers.SerializerMethodField()
    tag_ids = serializers.SerializerMethodField()
    location = GeoPointField(read_only=True)
    distance_km = serializers.SerializerMethodField()
    recipient_organization_id = serializers.SerializerMethodField()
    recipient_membership_id = serializers.SerializerMethodField()

    class Meta:
        model = ProfessionalProfile
        fields = (
            "id",
            "user_id",
            "display_name",
            "bio",
            "phone",
            "email_public",
            "is_available",
            "service_area_text",
            "location",
            "distance_km",
            "recipient_organization_id",
            "recipient_membership_id",
            "category_ids",
            "tag_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_category_ids(self, obj) -> list[int]:
        return list(obj.categories.values_list("id", flat=True))

    @extend_schema_field(serializers.ListField(child=serializers.IntegerField()))
    def get_tag_ids(self, obj) -> list[int]:
        return list(obj.tags.values_list("id", flat=True))

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_distance_km(self, obj) -> float | None:
        distance = getattr(obj, "distance", None)
        if distance is None:
            return None
        return round(distance.km, 2)

    def get_recipient_membership(self, obj):
        if hasattr(obj, "_recipient_membership"):
            return obj._recipient_membership

        membership = (
            OrganizationMembership.objects.filter(
                user=obj.user,
                status=OrganizationMembership.Statuses.ACTIVE,
                organization__kind=Organization.Kinds.PROFESSIONAL,
                organization__status=Organization.Statuses.ACTIVE,
                organization__plan__can_receive_cases=True,
            )
            .select_related("organization")
            .order_by("organization__name", "id")
            .first()
        )
        obj._recipient_membership = membership
        return membership

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_recipient_organization_id(self, obj) -> int | None:
        membership = self.get_recipient_membership(obj)
        return membership.organization_id if membership is not None else None

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_recipient_membership_id(self, obj) -> int | None:
        membership = self.get_recipient_membership(obj)
        return membership.id if membership is not None else None
