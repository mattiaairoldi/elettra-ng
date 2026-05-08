from rest_framework import serializers

from apps.cases.models import Case
from apps.identity.models import User
from apps.professionals.models import ProfessionalProfile

from .models import Appointment


APPOINTMENT_STATUS_TRANSITIONS = {
    Appointment.Statuses.REQUESTED: {
        Appointment.Statuses.CONFIRMED,
        Appointment.Statuses.CANCELLED,
        Appointment.Statuses.RESCHEDULED,
    },
    Appointment.Statuses.CONFIRMED: {
        Appointment.Statuses.COMPLETED,
        Appointment.Statuses.CANCELLED,
        Appointment.Statuses.RESCHEDULED,
    },
    Appointment.Statuses.RESCHEDULED: {
        Appointment.Statuses.CONFIRMED,
        Appointment.Statuses.CANCELLED,
    },
    Appointment.Statuses.COMPLETED: set(),
    Appointment.Statuses.CANCELLED: set(),
}

TERMINAL_CASE_STATUSES = {
    Case.Statuses.RESOLVED,
    Case.Statuses.CLOSED,
    Case.Statuses.CANCELLED,
}

TERMINAL_APPOINTMENT_STATUSES = {
    Appointment.Statuses.COMPLETED,
    Appointment.Statuses.CANCELLED,
}


class AppointmentSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="case.id", read_only=True)
    professional_profile_id = serializers.IntegerField(source="professional_profile.id", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "case_id",
            "professional_profile_id",
            "scheduled_start_at",
            "scheduled_end_at",
            "status",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AppointmentWriteSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField()
    professional_profile_id = serializers.IntegerField()

    class Meta:
        model = Appointment
        fields = ("case_id", "professional_profile_id", "scheduled_start_at", "scheduled_end_at", "notes")

    def validate(self, attrs):
        request = self.context["request"]
        instance = self.instance

        if instance is not None and instance.status in TERMINAL_APPOINTMENT_STATUSES:
            raise serializers.ValidationError("Terminal appointments cannot be edited.")

        case_id = attrs.get("case_id", instance.case_id if instance is not None else None)
        professional_profile_id = attrs.get(
            "professional_profile_id",
            instance.professional_profile_id if instance is not None else None,
        )

        if case_id is None:
            raise serializers.ValidationError({"case_id": "This field is required."})
        if professional_profile_id is None:
            raise serializers.ValidationError({"professional_profile_id": "This field is required."})

        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist as exc:
            raise serializers.ValidationError({"case_id": "Invalid case."}) from exc
        if case.status in TERMINAL_CASE_STATUSES:
            raise serializers.ValidationError({"case_id": "Appointments cannot be created for a terminal case."})
        if request.user.role == "customer" and case.customer_user_id != request.user.id:
            raise serializers.ValidationError({"case_id": "You do not own this case."})
        if request.user.role == "professional" and case.assigned_professional_id != request.user.id:
            raise serializers.ValidationError({"case_id": "You do not have access to this case."})

        try:
            professional_profile = ProfessionalProfile.objects.get(id=professional_profile_id, is_available=True)
        except ProfessionalProfile.DoesNotExist as exc:
            raise serializers.ValidationError({"professional_profile_id": "Invalid professional profile."}) from exc
        if request.user.role == "professional" and professional_profile.user_id != request.user.id:
            raise serializers.ValidationError({"professional_profile_id": "You can only schedule appointments for your own profile."})
        if case.assigned_professional_id is not None and professional_profile.user_id != case.assigned_professional_id:
            raise serializers.ValidationError(
                {"professional_profile_id": "Professional profile does not match the case assignment."}
            )
        if (
            attrs.get("scheduled_end_at") is not None
            and attrs["scheduled_end_at"] < attrs["scheduled_start_at"]
        ):
            raise serializers.ValidationError({"scheduled_end_at": "End time must be after start time."})

        attrs["case"] = case
        attrs["professional_profile"] = professional_profile
        return attrs

    def create(self, validated_data):
        validated_data.pop("case_id")
        validated_data.pop("professional_profile_id")
        return Appointment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("case_id", None)
        validated_data.pop("professional_profile_id", None)
        validated_data.pop("case", None)
        validated_data.pop("professional_profile", None)
        return super().update(instance, validated_data)


class AppointmentStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Appointment.Statuses.choices)

    def validate(self, attrs):
        appointment = self.context["appointment"]
        request = self.context["request"]
        next_status = attrs["status"]

        if next_status == appointment.status:
            return attrs

        if request.user.role == User.Roles.CUSTOMER and next_status != Appointment.Statuses.CANCELLED:
            raise serializers.ValidationError({"status": "Customers can only cancel appointments."})

        if next_status not in APPOINTMENT_STATUS_TRANSITIONS[appointment.status]:
            raise serializers.ValidationError({"status": "Invalid status transition for this appointment."})

        return attrs
