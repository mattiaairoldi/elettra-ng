from django.urls import path

from .views import ProfessionalDetailView, ProfessionalListView


app_name = "professionals"

urlpatterns = [
    path("professionals", ProfessionalListView.as_view(), name="professional-list"),
    path("professionals/<int:pk>", ProfessionalDetailView.as_view(), name="professional-detail"),
]
