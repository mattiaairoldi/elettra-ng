from django.db.models import Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Organization, OrganizationMembership
from .serializers import (
    OrganizationCreateSerializer,
    OrganizationMembershipCreateSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)


class OrganizationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Organization.objects.all()

    def get_queryset(self):
        queryset = Organization.objects.select_related("plan", "personal_owner", "created_by_user").prefetch_related("memberships")
        user = self.request.user
        if user.role == "admin":
            return queryset
        return queryset.filter(
            memberships__user=user,
            memberships__status=OrganizationMembership.Statuses.ACTIVE,
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated])
    def memberships(self, request, pk=None):
        organization = self.get_object()
        if request.method == "GET":
            memberships = organization.memberships.select_related("user", "organization", "approved_by_user")
            return Response(OrganizationMembershipSerializer(memberships, many=True).data)

        serializer = OrganizationMembershipCreateSerializer(
            data=request.data,
            context={"request": request, "organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(OrganizationMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class OrganizationMembershipViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationMembershipSerializer
    queryset = OrganizationMembership.objects.all()

    def get_queryset(self):
        queryset = OrganizationMembership.objects.select_related("user", "organization", "approved_by_user")
        user = self.request.user
        if user.role == "admin":
            return queryset
        return queryset.filter(
            Q(user=user)
            | Q(
                organization__memberships__user=user,
                organization__memberships__status=OrganizationMembership.Statuses.ACTIVE,
                organization__memberships__scope=OrganizationMembership.Scopes.ORGANIZATION,
                organization__memberships__role__in={
                    OrganizationMembership.Roles.OWNER,
                    OrganizationMembership.Roles.ADMIN,
                },
            )
        ).distinct()

