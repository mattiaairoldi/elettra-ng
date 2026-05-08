from django.urls import path

from .views import FlowDetailView, FlowListView, FlowNodesListView, NodeDetailView, NodeOptionsListView


app_name = "troubleshooting"

urlpatterns = [
    path("flows", FlowListView.as_view(), name="flow-list"),
    path("flows/<int:pk>", FlowDetailView.as_view(), name="flow-detail"),
    path("flows/<int:pk>/nodes", FlowNodesListView.as_view(), name="flow-nodes"),
    path("nodes/<int:pk>", NodeDetailView.as_view(), name="node-detail"),
    path("nodes/<int:pk>/options", NodeOptionsListView.as_view(), name="node-options"),
]
