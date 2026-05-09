from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    DiagnosticAdviceStep,
    DiagnosticChapter,
    DiagnosticChapterOption,
    DiagnosticFlow,
    DiagnosticNode,
    DiagnosticOption,
)
from .serializers import (
    DiagnosticAdviceFeedbackSerializer,
    DiagnosticAdviceStepSerializer,
    DiagnosticChapterOptionSerializer,
    DiagnosticChapterSerializer,
    DiagnosticFlowSerializer,
    DiagnosticNodeSerializer,
    DiagnosticOptionSerializer,
)


class PublicChapterQuerysetMixin:
    def get_public_chapters_queryset(self):
        return (
            DiagnosticChapter.objects.filter(
                is_public=True,
                status=DiagnosticChapter.Statuses.PUBLISHED,
            )
            .select_related("category")
            .prefetch_related("options", "safety_rules")
        )


class ChapterListView(PublicChapterQuerysetMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticChapterSerializer

    def get_queryset(self):
        queryset = self.get_public_chapters_queryset()

        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        search_query = self.request.query_params.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(slug__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        return queryset


class ChapterDetailView(PublicChapterQuerysetMixin, generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticChapterSerializer

    def get_queryset(self):
        return self.get_public_chapters_queryset()


class ChapterOptionsListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticChapterOptionSerializer

    def get_queryset(self):
        return DiagnosticChapterOption.objects.filter(
            chapter_id=self.kwargs["pk"],
            chapter__is_public=True,
            chapter__status=DiagnosticChapter.Statuses.PUBLISHED,
            is_active=True,
        ).select_related("chapter")


class ChapterAdviceStepsListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticAdviceStepSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("option_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
        ],
        responses={200: DiagnosticAdviceStepSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = DiagnosticAdviceStep.objects.filter(
            chapter_id=self.kwargs["pk"],
            chapter__is_public=True,
            chapter__status=DiagnosticChapter.Statuses.PUBLISHED,
            is_active=True,
        ).select_related("chapter", "chapter_option")

        option_id = self.request.query_params.get("option_id")
        if option_id:
            queryset = queryset.filter(Q(chapter_option_id=option_id) | Q(chapter_option__isnull=True))
        else:
            queryset = queryset.filter(chapter_option__isnull=True)

        return queryset


class AdviceStepDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DiagnosticAdviceStepSerializer
    queryset = DiagnosticAdviceStep.objects.filter(
        chapter__is_public=True,
        chapter__status=DiagnosticChapter.Statuses.PUBLISHED,
        is_active=True,
    ).select_related("chapter", "chapter_option")


class AdviceStepFeedbackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=DiagnosticAdviceFeedbackSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request, pk):
        advice_step = generics.get_object_or_404(
            DiagnosticAdviceStep.objects.filter(
                chapter__is_public=True,
                chapter__status=DiagnosticChapter.Statuses.PUBLISHED,
                is_active=True,
            ).select_related("chapter", "chapter_option"),
            pk=pk,
        )
        serializer = DiagnosticAdviceFeedbackSerializer(
            data=request.data,
            context={"request": request, "advice_step": advice_step},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.save_feedback())


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
