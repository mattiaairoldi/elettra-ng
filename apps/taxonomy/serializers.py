from rest_framework import serializers

from .models import Category, Tag


class CategorySerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source="parent.id", read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "parent_id",
            "is_active",
            "sort_order",
        )
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source="category.id", read_only=True)

    class Meta:
        model = Tag
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category_id",
            "is_active",
        )
        read_only_fields = fields
