from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership

from .models import Attachment
from .serializers import AttachmentSerializer, AttachmentUploadSerializer


class AttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Attachment.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = Attachment.objects.select_related(
            "uploaded_by_user",
            "case",
            "asset",
            "asset__property",
        )
        if user.role != "admin":
            queryset = queryset.filter(
                Q(case__customer_user=user)
                | Q(case__assigned_professional=user)
                | Q(
                    case__owner_organization__memberships__user=user,
                    case__owner_organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
                )
                | Q(
                    asset__property__organization__memberships__user=user,
                    asset__property__organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
                )
            ).distinct()
        case_id = self.request.query_params.get("case_id")
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)
        return queryset

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
