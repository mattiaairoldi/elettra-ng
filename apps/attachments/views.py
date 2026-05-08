from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from .models import Attachment
from .serializers import AttachmentSerializer, AttachmentUploadSerializer


class AttachmentViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Attachment.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Attachment.objects.select_related("uploaded_by_user", "case", "asset", "asset__property")
        if user.role == "professional":
            return Attachment.objects.filter(case__assigned_professional=user).select_related(
                "uploaded_by_user", "case", "asset", "asset__property"
            )
        return Attachment.objects.filter(
            Q(case__customer_user=user) | Q(asset__property__owner_user=user)
        ).select_related("uploaded_by_user", "case", "asset", "asset__property")

    def get_serializer_class(self):
        if self.action == "create":
            return AttachmentUploadSerializer
        return AttachmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(AttachmentSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        instance.file.delete(save=False)
        instance.delete()
