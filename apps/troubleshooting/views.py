from django.db.models import Q
from rest_framework import generics, permissions

from .models import DiagnosticFlow, DiagnosticNode, DiagnosticOption
from .serializers import DiagnosticFlowSerializer, DiagnosticNodeSerializer, DiagnosticOptionSerializer


class PublicFlowQuerysetMixin:
    def get_public_flows_queryset(self):
        return DiagnosticFlow.objects.filter(
            is_public=True,
            status=DiagnosticFlow.Statuses.PUBLISHED,
            category__is_active=True,
        ).select_related("category")


class FlowListView(PublicFlowQuerysetMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticFlowSerializer

    def get_queryset(self):
        queryset = self.get_public_flows_queryset()

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        search_query = self.request.query_params.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(slug__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        return queryset


class FlowDetailView(PublicFlowQuerysetMixin, generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticFlowSerializer

    def get_queryset(self):
        return self.get_public_flows_queryset()


class FlowNodesListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticNodeSerializer

    def get_queryset(self):
        return DiagnosticNode.objects.filter(
            flow_id=self.kwargs["pk"],
            flow__is_public=True,
            flow__status=DiagnosticFlow.Statuses.PUBLISHED,
        ).select_related("flow")


class NodeDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticNodeSerializer
    queryset = DiagnosticNode.objects.filter(
        flow__is_public=True,
        flow__status=DiagnosticFlow.Statuses.PUBLISHED,
    ).select_related("flow")


class NodeOptionsListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticOptionSerializer

    def get_queryset(self):
        return DiagnosticOption.objects.filter(
            from_node_id=self.kwargs["pk"],
            from_node__flow__is_public=True,
            from_node__flow__status=DiagnosticFlow.Statuses.PUBLISHED,
        ).select_related("from_node", "to_node")
