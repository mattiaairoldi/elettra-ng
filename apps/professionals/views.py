from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q
from rest_framework import generics, permissions

from .models import ProfessionalProfile
from .serializers import ProfessionalProfileSerializer


class ProfessionalListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProfessionalProfileSerializer

    def get_queryset(self):
        queryset = ProfessionalProfile.objects.filter(
            is_available=True,
            user__is_active=True,
            user__role="professional",
        ).prefetch_related("categories", "tags")

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        tag_id = self.request.query_params.get("tag_id")
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)

        search_query = self.request.query_params.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(display_name__icontains=search_query)
                | Q(bio__icontains=search_query)
                | Q(service_area_text__icontains=search_query)
                | Q(categories__name__icontains=search_query)
                | Q(tags__name__icontains=search_query)
            )

        latitude = self.request.query_params.get("latitude", self.request.query_params.get("lat"))
        longitude = self.request.query_params.get("longitude", self.request.query_params.get("lng"))
        if latitude is not None and longitude is not None:
            try:
                user_location = Point(float(longitude), float(latitude), srid=4326)
            except (TypeError, ValueError):
                pass
            else:
                queryset = queryset.filter(location__isnull=False).annotate(
                    distance=Distance("location", user_location)
                ).order_by("distance", "id")

        return queryset.distinct()


class ProfessionalDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProfessionalProfileSerializer
    queryset = ProfessionalProfile.objects.filter(
        is_available=True,
        user__is_active=True,
        user__role="professional",
    ).prefetch_related("categories", "tags")
