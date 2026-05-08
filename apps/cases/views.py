from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .events import create_case_event, update_case_status
from .models import Asset, Case, CaseEvent, CaseNote, Property
from .permissions import IsAdminUserRole
from .serializers import (
    AssetSerializer,
    CaseAssignSerializer,
    CaseEventSerializer,
    CaseNoteSerializer,
    CaseSerializer,
    CaseStatusSerializer,
    CaseTroubleshootingProgressSerializer,
    CaseTroubleshootingStartSerializer,
    CaseWriteSerializer,
    PropertySerializer,
)
from apps.organizations.models import OrganizationMembership


def build_case_queryset(user):
    if user.role == "admin":
        return Case.objects.all()
    if user.role == "professional":
        return Case.objects.filter(assigned_professional=user)
    return Case.objects.filter(customer_user=user)


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
        queryset = Asset.objects.select_related("property", "category", "property__owner_user", "property__organization")
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
