from django.urls import path

from .views import CategoryDetailView, CategoryListView, TagDetailView, TagListView


app_name = "taxonomy"

urlpatterns = [
    path("categories", CategoryListView.as_view(), name="category-list"),
    path("categories/<int:pk>", CategoryDetailView.as_view(), name="category-detail"),
    path("tags", TagListView.as_view(), name="tag-list"),
    path("tags/<int:pk>", TagDetailView.as_view(), name="tag-detail"),
]
