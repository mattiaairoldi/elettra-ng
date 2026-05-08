from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.models import OrganizationMembership

from .models import Conversation
from .serializers import (
    ConversationCreateSerializer,
    ConversationPostCreateSerializer,
    ConversationPostSerializer,
    ConversationSerializer,
)


class ConversationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conversation.objects.all()

    def get_queryset(self):
        queryset = Conversation.objects.select_related(
            "case",
            "case_share_request",
            "created_by_user",
        ).prefetch_related(
            "participants",
            "participants__user",
            "participants__organization",
            "participants__membership",
        )
        user = self.request.user
        if user.role == "admin":
            return queryset
        return queryset.filter(
            Q(participants__user=user, participants__status="active")
            | Q(
                participants__membership__user=user,
                participants__membership__status=OrganizationMembership.Statuses.ACTIVE,
                participants__status="active",
            )
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return ConversationCreateSerializer
        return ConversationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated])
    def posts(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            serializer = ConversationPostSerializer(
                conversation.posts.select_related("author_user", "author_membership"),
                many=True,
            )
            return Response(serializer.data)

        serializer = ConversationPostCreateSerializer(
            data=request.data,
            context={"request": request, "conversation": conversation},
        )
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        return Response(ConversationPostSerializer(post).data, status=status.HTTP_201_CREATED)

