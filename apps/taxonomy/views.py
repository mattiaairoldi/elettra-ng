from django.db.models import Q
from rest_framework import generics, permissions

from .models import Category, Tag
from .serializers import CategorySerializer, TagSerializer


def parse_bool_param(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


class CategoryListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True).select_related("parent")

        parent_id = self.request.query_params.get("parent_id")
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        is_root = parse_bool_param(self.request.query_params.get("is_root"))
        if is_root is True:
            queryset = queryset.filter(parent__isnull=True)
        elif is_root is False:
            queryset = queryset.filter(parent__isnull=False)

        return queryset


class CategoryDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(is_active=True).select_related("parent")


class TagListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.filter(is_active=True).select_related("category")

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        search_query = self.request.query_params.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(slug__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        return queryset


class TagDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TagSerializer
    queryset = Tag.objects.filter(is_active=True).select_related("category")
