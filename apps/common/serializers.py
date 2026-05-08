from django.contrib.gis.geos import Point
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers


geo_point_schema = inline_serializer(
    name="GeoPoint",
    fields={
        "latitude": serializers.FloatField(),
        "longitude": serializers.FloatField(),
    },
)


@extend_schema_field(geo_point_schema)
class GeoPointField(serializers.Field):
    default_error_messages = {
        "invalid": "Expected an object with latitude and longitude.",
        "required": "Both latitude and longitude are required.",
        "latitude": "Latitude must be between -90 and 90.",
        "longitude": "Longitude must be between -180 and 180.",
    }

    def to_representation(self, value):
        if value is None:
            return None
        return {
            "latitude": value.y,
            "longitude": value.x,
        }

    def to_internal_value(self, data):
        if data is None:
            return None
        if not isinstance(data, dict):
            self.fail("invalid")

        raw_latitude = data.get("latitude", data.get("lat"))
        raw_longitude = data.get("longitude", data.get("lng"))
        if raw_latitude is None or raw_longitude is None:
            self.fail("required")

        try:
            latitude = float(raw_latitude)
            longitude = float(raw_longitude)
        except (TypeError, ValueError):
            self.fail("invalid")

        if not -90 <= latitude <= 90:
            self.fail("latitude")
        if not -180 <= longitude <= 180:
            self.fail("longitude")

        return Point(longitude, latitude, srid=4326)
