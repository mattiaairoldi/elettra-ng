import calendar

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .access import build_case_visibility_filter, user_can_respond_to_share_request, user_can_share_case
from .events import create_case_event, update_case_status
from .models import (
    Asset,
    AssetMaintenanceEvent,
    AssetMaintenanceReminder,
    Case,
    CaseEvent,
    CaseNote,
    CaseShareRequest,
    Property,
)
from .permissions import IsAdminUserRole
from .share_services import accept_case_share_request, reject_case_share_request, revoke_case_share_request
from .serializers import (
    AssetSerializer,
    AssetMaintenanceEventSerializer,
    AssetMaintenanceReminderSerializer,
    CaseAssignSerializer,
    CaseEventSerializer,
    CaseNoteSerializer,
    CaseShareRequestCreateSerializer,
    CaseShareRequestRejectSerializer,
    CaseShareRequestSerializer,
    CaseSerializer,
    CaseStatusSerializer,
    CaseTroubleshootingProgressSerializer,
    CaseTroubleshootingStartSerializer,
    CaseWriteSerializer,
    PropertySerializer,
)
from apps.organizations.models import OrganizationMembership


def build_case_queryset(user):
    queryset = Case.objects.all()
    if user.role == "admin":
        return queryset
    return queryset.filter(build_case_visibility_filter(user)).distinct()


def build_property_asset_visibility_filter(user):
    if user.role == "admin":
        return Q()
    active_membership_filter = Q(
        property__organization__memberships__user=user,
        property__organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
    )
    active_asset_membership_filter = Q(
        asset__property__organization__memberships__user=user,
        asset__property__organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
    )
    return active_membership_filter | active_asset_membership_filter


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class PropertyViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertySerializer
    queryset = Property.objects.all()

    def get_queryset(self):
        queryset = Property.objects.select_related("owner_user", "organization")
        if self.request.user.role != "admin":
            queryset = queryset.filter(
                organization__memberships__user=self.request.user,
                organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
            ).distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner_user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(PropertySerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(PropertySerializer(self.get_object()).data, status=response.status_code)


class AssetViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssetSerializer
    queryset = Asset.objects.all()

    def get_queryset(self):
        queryset = Asset.objects.select_related(
            "property",
            "category",
            "property__owner_user",
            "property__organization",
        )
        if self.request.user.role != "admin":
            queryset = queryset.filter(
                property__organization__memberships__user=self.request.user,
                property__organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
            ).distinct()

        property_id = self.request.query_params.get("property_id")
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(AssetSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(AssetSerializer(self.get_object()).data, status=response.status_code)


class AssetMaintenanceEventViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssetMaintenanceEventSerializer
    queryset = AssetMaintenanceEvent.objects.all()

    def get_queryset(self):
        queryset = AssetMaintenanceEvent.objects.select_related(
            "asset",
            "asset__property",
            "property",
            "created_by_user",
        )
        if self.request.user.role != "admin":
            queryset = queryset.filter(build_property_asset_visibility_filter(self.request.user)).distinct()

        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)

        property_id = self.request.query_params.get("property_id")
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(AssetMaintenanceEventSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(AssetMaintenanceEventSerializer(self.get_object()).data, status=response.status_code)


class AssetMaintenanceReminderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssetMaintenanceReminderSerializer
    queryset = AssetMaintenanceReminder.objects.all()

    def get_queryset(self):
        queryset = AssetMaintenanceReminder.objects.select_related(
            "asset",
            "asset__property",
            "property",
            "created_by_user",
        )
        if self.request.user.role != "admin":
            queryset = queryset.filter(build_property_asset_visibility_filter(self.request.user)).distinct()

        asset_id = self.request.query_params.get("asset_id")
        if asset_id:
            queryset = queryset.filter(asset_id=asset_id)

        property_id = self.request.query_params.get("property_id")
        if property_id:
            queryset = queryset.filter(property_id=property_id)

        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        due_before = self.request.query_params.get("due_before")
        if due_before:
            queryset = queryset.filter(due_at__lte=due_before)

        due_after = self.request.query_params.get("due_after")
        if due_after:
            queryset = queryset.filter(due_at__gte=due_after)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(AssetMaintenanceReminderSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(AssetMaintenanceReminderSerializer(self.get_object()).data, status=response.status_code)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        if reminder.status != AssetMaintenanceReminder.Statuses.ACTIVE:
            return Response({"detail": "Only active reminders can be completed."}, status=status.HTTP_400_BAD_REQUEST)

        completed_at = timezone.now()
        update_fields = ["last_completed_at", "status", "updated_at"]
        reminder.last_completed_at = completed_at

        recurrence_months = {
            AssetMaintenanceReminder.RecurrenceRules.MONTHLY: 1,
            AssetMaintenanceReminder.RecurrenceRules.QUARTERLY: 3,
            AssetMaintenanceReminder.RecurrenceRules.SEMIANNUAL: 6,
            AssetMaintenanceReminder.RecurrenceRules.ANNUAL: 12,
        }
        months = recurrence_months.get(reminder.recurrence_rule)
        if months is None:
            reminder.status = AssetMaintenanceReminder.Statuses.COMPLETED
        else:
            next_due_at = add_months(reminder.due_at, months)
            while next_due_at <= completed_at:
                next_due_at = add_months(next_due_at, months)
            reminder.due_at = next_due_at
            reminder.status = AssetMaintenanceReminder.Statuses.ACTIVE
            update_fields.append("due_at")

        reminder.save(update_fields=update_fields)
        return Response({"reminder": AssetMaintenanceReminderSerializer(reminder).data})


class CaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Case.objects.all()

    def get_queryset(self):
        queryset = build_case_queryset(self.request.user).select_related(
            "customer_user",
            "owner_organization",
            "assigned_professional",
            "category",
            "property",
            "asset",
            "troubleshooting_flow",
            "current_diagnostic_node",
        )
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        assigned_to_me = self.request.query_params.get("assigned_to_me")
        if assigned_to_me and assigned_to_me.lower() in {"1", "true", "yes", "on"}:
            queryset = queryset.filter(assigned_professional=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action in {"create", "partial_update", "update"}:
            return CaseWriteSerializer
        return CaseSerializer

    def perform_create(self, serializer):
        case = serializer.save()
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.CASE_CREATED,
            actor_user=self.request.user,
            payload={"status": case.status, "source": case.source},
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(CaseSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(CaseSerializer(self.get_object()).data, status=response.status_code)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAdminUserRole])
    def assign(self, request, pk=None):
        case = self.get_object()
        serializer = CaseAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        previous_assigned_professional_id = case.assigned_professional_id
        case.assigned_professional = serializer.context.get("professional_user")
        case.save(update_fields=["assigned_professional", "updated_at"])
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.PROFESSIONAL_ASSIGNED,
            actor_user=request.user,
            payload={
                "previous_assigned_professional_id": previous_assigned_professional_id,
                "assigned_professional_id": case.assigned_professional_id,
            },
        )
        return Response({"case": CaseSerializer(case).data})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def status(self, request, pk=None):
        case = self.get_object()
        serializer = CaseStatusSerializer(data=request.data, context={"request": request, "case": case})
        serializer.is_valid(raise_exception=True)
        update_case_status(case, serializer.validated_data["status"], actor_user=request.user)
        return Response({"case": CaseSerializer(case).data})

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated], url_path="notes")
    def notes(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            queryset = case.notes.select_related("author_user")
            serializer = CaseNoteSerializer(queryset, many=True)
            return Response(serializer.data)

        serializer = CaseNoteSerializer(data=request.data, context={"request": request, "case": case})
        serializer.is_valid(raise_exception=True)
        note = serializer.save()
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.NOTE_ADDED,
            actor_user=request.user,
            payload={"note_id": note.id, "note_type": note.note_type, "is_internal": note.is_internal},
        )
        return Response(CaseNoteSerializer(note).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated], url_path="events")
    def events(self, request, pk=None):
        case = self.get_object()
        serializer = CaseEventSerializer(case.events.select_related("actor_user"), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated], url_path="share-requests")
    def share_requests(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            queryset = case.share_requests.select_related(
                "case",
                "requester_user",
                "recipient_organization",
                "recipient_membership",
                "recipient_membership__user",
                "accepted_by_user",
                "rejected_by_user",
                "revoked_by_user",
            )
            serializer = CaseShareRequestSerializer(queryset, many=True)
            return Response(serializer.data)

        if not user_can_share_case(request.user, case):
            return Response({"detail": "You cannot share this case."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CaseShareRequestCreateSerializer(data=request.data, context={"request": request, "case": case})
        serializer.is_valid(raise_exception=True)
        share_request = serializer.save()
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.CASE_SHARE_REQUEST_CREATED,
            actor_user=request.user,
            payload={
                "share_request_id": share_request.id,
                "recipient_organization_id": share_request.recipient_organization_id,
                "recipient_membership_id": share_request.recipient_membership_id,
                "share_scope": share_request.share_scope,
            },
        )
        from apps.notifications.services import notify_case_share_request_created

        notify_case_share_request_created(share_request, actor_user=request.user)
        return Response(CaseShareRequestSerializer(share_request).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="troubleshooting/start")
    def troubleshooting_start(self, request, pk=None):
        case = self.get_object()
        serializer = CaseTroubleshootingStartSerializer(data=request.data, context={"case": case})
        serializer.is_valid(raise_exception=True)
        flow = serializer.context["flow"]
        previous_status = case.status
        case.troubleshooting_flow = flow
        case.status = Case.Statuses.IN_DIAGNOSIS
        case.source = Case.Sources.TROUBLESHOOTING
        case.current_diagnostic_node = flow.nodes.filter(is_entrypoint=True).order_by("sort_order", "id").first()
        case.save(update_fields=["troubleshooting_flow", "status", "source", "current_diagnostic_node", "updated_at"])
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.TROUBLESHOOTING_STARTED,
            actor_user=request.user,
            payload={
                "flow_id": flow.id,
                "current_node_id": case.current_diagnostic_node_id,
                "previous_status": previous_status,
                "status": case.status,
            },
        )
        return Response({"case": CaseSerializer(case).data})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="troubleshooting/progress")
    def troubleshooting_progress(self, request, pk=None):
        case = self.get_object()
        serializer = CaseTroubleshootingProgressSerializer(data=request.data, context={"case": case})
        serializer.is_valid(raise_exception=True)
        node = serializer.validated_data["node"]
        option = serializer.validated_data.get("option")
        previous_node_id = case.current_diagnostic_node_id
        case.current_diagnostic_node = option.to_node if option is not None and option.to_node_id is not None else node
        case.save(update_fields=["current_diagnostic_node", "updated_at"])
        create_case_event(
            case=case,
            event_type=CaseEvent.EventTypes.TROUBLESHOOTING_PROGRESS,
            actor_user=request.user,
            payload={
                "previous_node_id": previous_node_id,
                "node_id": node.id,
                "option_id": option.id if option is not None else None,
                "current_node_id": case.current_diagnostic_node_id,
            },
        )
        return Response({"case": CaseSerializer(case).data})


class CaseShareRequestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CaseShareRequestSerializer
    queryset = CaseShareRequest.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = CaseShareRequest.objects.select_related(
            "case",
            "requester_user",
            "recipient_organization",
            "recipient_membership",
            "recipient_membership__user",
            "accepted_by_user",
            "rejected_by_user",
            "revoked_by_user",
        )
        if user.role == "admin":
            visible_queryset = queryset
        else:
            visible_queryset = queryset.filter(
                Q(case__customer_user=user)
                | Q(
                    case__owner_organization__memberships__user=user,
                    case__owner_organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
                )
                | Q(
                    recipient_membership__user=user,
                    recipient_membership__status=OrganizationMembership.Statuses.ACTIVE,
                )
                | Q(
                    recipient_organization__memberships__user=user,
                    recipient_organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
                    recipient_organization__memberships__scope=OrganizationMembership.Scopes.ORGANIZATION,
                )
            ).distinct()

        status_value = self.request.query_params.get("status")
        if status_value:
            visible_queryset = visible_queryset.filter(status=status_value)
        return visible_queryset

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request, pk=None):
        share_request = self.get_object()
        if share_request.status != CaseShareRequest.Statuses.PENDING:
            return Response({"detail": "Only pending share requests can be accepted."}, status=status.HTTP_400_BAD_REQUEST)
        if not user_can_respond_to_share_request(request.user, share_request):
            return Response({"detail": "You cannot accept this share request."}, status=status.HTTP_403_FORBIDDEN)
        conversation = accept_case_share_request(share_request, request.user)
        share_request.refresh_from_db()
        return Response(
            {
                "share_request": CaseShareRequestSerializer(share_request).data,
                "conversation_id": conversation.id,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        share_request = self.get_object()
        if share_request.status != CaseShareRequest.Statuses.PENDING:
            return Response({"detail": "Only pending share requests can be rejected."}, status=status.HTTP_400_BAD_REQUEST)
        if not user_can_respond_to_share_request(request.user, share_request):
            return Response({"detail": "You cannot reject this share request."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CaseShareRequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reject_case_share_request(share_request, request.user, reason=serializer.validated_data.get("reason", ""))
        share_request.refresh_from_db()
        return Response({"share_request": CaseShareRequestSerializer(share_request).data})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def revoke(self, request, pk=None):
        share_request = self.get_object()
        if share_request.status != CaseShareRequest.Statuses.ACCEPTED:
            return Response({"detail": "Only accepted share requests can be revoked."}, status=status.HTTP_400_BAD_REQUEST)
        if not user_can_share_case(request.user, share_request.case):
            return Response({"detail": "You cannot revoke this share request."}, status=status.HTTP_403_FORBIDDEN)
        revoke_case_share_request(share_request, request.user)
        share_request.refresh_from_db()
        return Response({"share_request": CaseShareRequestSerializer(share_request).data})
