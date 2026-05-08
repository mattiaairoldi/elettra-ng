from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.cases.events import create_case_event, update_case_status
from apps.cases.models import Case, CaseEvent

from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentStatusSerializer, AppointmentWriteSerializer


def build_appointment_queryset(user):
    if user.role == "admin":
        return Appointment.objects.all()
    if user.role == "professional":
        return Appointment.objects.filter(professional_profile__user=user)
    return Appointment.objects.filter(case__customer_user=user)


class AppointmentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Appointment.objects.all()

    def get_queryset(self):
        queryset = build_appointment_queryset(self.request.user).select_related(
            "case",
            "professional_profile",
            "professional_profile__user",
        )

        case_id = self.request.query_params.get("case_id")
        if case_id:
            queryset = queryset.filter(case_id=case_id)

        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return AppointmentWriteSerializer
        return AppointmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        create_case_event(
            case=serializer.instance.case,
            event_type=CaseEvent.EventTypes.APPOINTMENT_CREATED,
            actor_user=request.user,
            payload={
                "appointment_id": serializer.instance.id,
                "professional_profile_id": serializer.instance.professional_profile_id,
                "status": serializer.instance.status,
            },
        )
        return Response(AppointmentSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(AppointmentSerializer(self.get_object()).data, status=response.status_code)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def status(self, request, pk=None):
        appointment = self.get_object()
        serializer = AppointmentStatusSerializer(
            data=request.data,
            context={"appointment": appointment, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        previous_status = appointment.status
        appointment.status = serializer.validated_data["status"]
        appointment.save(update_fields=["status", "updated_at"])
        create_case_event(
            case=appointment.case,
            event_type=CaseEvent.EventTypes.APPOINTMENT_STATUS_CHANGED,
            actor_user=request.user,
            payload={
                "appointment_id": appointment.id,
                "previous_status": previous_status,
                "status": appointment.status,
            },
        )
        if appointment.status in {Appointment.Statuses.CONFIRMED, Appointment.Statuses.RESCHEDULED}:
            if appointment.case.status != Case.Statuses.SCHEDULED:
                update_case_status(
                    appointment.case,
                    Case.Statuses.SCHEDULED,
                    actor_user=request.user,
                    payload={"reason": "appointment_status", "appointment_id": appointment.id},
                )
        elif appointment.status == Appointment.Statuses.CANCELLED and appointment.case.status == Case.Statuses.SCHEDULED:
            has_active_appointments = appointment.case.appointments.exclude(id=appointment.id).filter(
                status__in={
                    Appointment.Statuses.REQUESTED,
                    Appointment.Statuses.CONFIRMED,
                    Appointment.Statuses.RESCHEDULED,
                }
            ).exists()
            if not has_active_appointments:
                fallback_status = (
                    Case.Statuses.WAITING_PROFESSIONAL
                    if appointment.case.assigned_professional_id is not None
                    else Case.Statuses.OPEN
                )
                update_case_status(
                    appointment.case,
                    fallback_status,
                    actor_user=request.user,
                    payload={"reason": "appointment_status", "appointment_id": appointment.id},
                )
        return Response({"appointment": AppointmentSerializer(appointment).data})
