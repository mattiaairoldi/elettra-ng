from django.urls import path

from .views import (
    AdviceStepDetailView,
    AdviceStepFeedbackView,
    ChapterAdviceStepsListView,
    ChapterDetailView,
    ChapterListView,
    ChapterOptionsListView,
    FlowDetailView,
    FlowListView,
    FlowNodesListView,
    NodeDetailView,
    NodeOptionsListView,
)


app_name = "troubleshooting"

urlpatterns = [
    path("diagnostic-chapters", ChapterListView.as_view(), name="chapter-list"),
    path("diagnostic-chapters/<int:pk>", ChapterDetailView.as_view(), name="chapter-detail"),
    path("diagnostic-chapters/<int:pk>/options", ChapterOptionsListView.as_view(), name="chapter-options"),
    path(
        "diagnostic-chapters/<int:pk>/advice-steps",
        ChapterAdviceStepsListView.as_view(),
        name="chapter-advice-steps",
    ),
    path("diagnostic-advice-steps/<int:pk>", AdviceStepDetailView.as_view(), name="advice-step-detail"),
    path("diagnostic-advice-steps/<int:pk>/feedback", AdviceStepFeedbackView.as_view(), name="advice-step-feedback"),
    path("flows", FlowListView.as_view(), name="flow-list"),
    path("flows/<int:pk>", FlowDetailView.as_view(), name="flow-detail"),
    path("flows/<int:pk>/nodes", FlowNodesListView.as_view(), name="flow-nodes"),
    path("nodes/<int:pk>", NodeDetailView.as_view(), name="node-detail"),
    path("nodes/<int:pk>/options", NodeOptionsListView.as_view(), name="node-options"),
]
