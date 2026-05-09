from django.utils import timezone
from rest_framework import serializers

from .models import DeviceInstallation, Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_user_id = serializers.IntegerField(source="recipient_user.id", read_only=True)
    actor_user_id = serializers.IntegerField(source="actor_user.id", read_only=True, allow_null=True)
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "recipient_user_id",
            "actor_user_id",
            "notification_type",
            "title",
            "body",
            "priority",
            "target_type",
            "target_id",
            "deep_link",
            "metadata_json",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class NotificationSummarySerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()


class DeviceInstallationSerializer(serializers.ModelSerializer):
    installation_id = serializers.UUIDField(required=False)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    push_token = serializers.CharField(required=False, allow_blank=True, write_only=True, max_length=512)

    class Meta:
        model = DeviceInstallation
        fields = (
            "id",
            "installation_id",
            "user_id",
            "platform",
            "push_provider",
            "push_token",
            "app_version",
            "device_model",
            "locale",
            "timezone",
            "is_active",
            "last_seen_at",
            "deactivated_at",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user_id",
            "is_active",
            "last_seen_at",
            "deactivated_at",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "installation_id": {"required": False},
            "app_version": {"required": False, "allow_blank": True},
            "device_model": {"required": False, "allow_blank": True},
            "locale": {"required": False, "allow_blank": True},
            "timezone": {"required": False, "allow_blank": True},
            "metadata_json": {"required": False},
        }

    def validate_installation_id(self, value):
        request = self.context["request"]
        existing = DeviceInstallation.objects.filter(installation_id=value).first()
        if existing is not None and existing.user_id != request.user.id:
            raise serializers.ValidationError("Installation belongs to another user.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        installation_id = validated_data.get("installation_id")
        defaults = {
            **validated_data,
            "user": request.user,
            "is_active": True,
            "last_seen_at": timezone.now(),
            "deactivated_at": None,
        }

        if installation_id is not None:
            installation, _created = DeviceInstallation.objects.update_or_create(
                user=request.user,
                installation_id=installation_id,
                defaults=defaults,
            )
            return installation

        return DeviceInstallation.objects.create(**defaults)

    def update(self, instance, validated_data):
        validated_data.pop("installation_id", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.is_active = True
        instance.last_seen_at = timezone.now()
        instance.deactivated_at = None
        instance.save()
        return instance
