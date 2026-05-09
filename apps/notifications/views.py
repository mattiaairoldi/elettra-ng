from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DeviceInstallation, Notification
from .serializers import DeviceInstallationSerializer, NotificationSerializer, NotificationSummarySerializer


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_queryset(self):
        queryset = Notification.objects.select_related("recipient_user", "actor_user").filter(
            recipient_user=self.request.user,
        )

        unread = self.request.query_params.get("unread")
        if unread and unread.lower() in {"1", "true", "yes", "on"}:
            queryset = queryset.filter(read_at__isnull=True)

        notification_type = self.request.query_params.get("type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        target_type = self.request.query_params.get("target_type")
        if target_type:
            queryset = queryset.filter(target_type=target_type)

        return queryset

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def summary(self, request):
        serializer = NotificationSummarySerializer(
            {"unread_count": self.get_queryset().filter(read_at__isnull=True).count()}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        return Response({"notification": NotificationSerializer(notification).data})

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="mark-all-read")
    def mark_all_read(self, request):
        now = timezone.now()
        updated_count = self.get_queryset().filter(read_at__isnull=True).update(read_at=now, updated_at=now)
        return Response({"updated_count": updated_count})


class DeviceInstallationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceInstallationSerializer
    queryset = DeviceInstallation.objects.all()

    def get_queryset(self):
        queryset = DeviceInstallation.objects.filter(user=self.request.user)
        active = self.request.query_params.get("active")
        if active and active.lower() in {"1", "true", "yes", "on"}:
            queryset = queryset.filter(is_active=True)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(DeviceInstallationSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(DeviceInstallationSerializer(self.get_object()).data, status=response.status_code)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        now = timezone.now()
        instance.is_active = False
        instance.deactivated_at = now
        instance.last_seen_at = now
        instance.save(update_fields=["is_active", "deactivated_at", "last_seen_at", "updated_at"])
