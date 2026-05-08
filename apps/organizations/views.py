from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Organization, OrganizationInvitation, OrganizationMembership
from .permissions import user_can_manage_organization
from .serializers import (
    OrganizationCreateSerializer,
    OrganizationInvitationAcceptSerializer,
    OrganizationInvitationCreateSerializer,
    OrganizationInvitationSerializer,
    OrganizationMembershipCreateSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
)
from .tasks import send_organization_invitation_email_task


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

    @action(detail=True, methods=["get", "post"], permission_classes=[permissions.IsAuthenticated])
    def invitations(self, request, pk=None):
        organization = self.get_object()
        if not user_can_manage_organization(request.user, organization):
            return Response({"detail": "You cannot manage this organization."}, status=status.HTTP_403_FORBIDDEN)

        if request.method == "GET":
            invitations = organization.invitations.select_related(
                "organization",
                "invited_by_user",
                "accepted_by_user",
                "accepted_membership",
                "revoked_by_user",
            )
            return Response(OrganizationInvitationSerializer(invitations, many=True).data)

        serializer = OrganizationInvitationCreateSerializer(
            data=request.data,
            context={"request": request, "organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        send_organization_invitation_email_task.delay(invitation.id)
        return Response(OrganizationInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


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


class OrganizationInvitationViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationInvitationSerializer
    queryset = OrganizationInvitation.objects.all()

    def get_queryset(self):
        queryset = OrganizationInvitation.objects.select_related(
            "organization",
            "invited_by_user",
            "accepted_by_user",
            "accepted_membership",
            "revoked_by_user",
        )
        user = self.request.user
        if user.role == "admin":
            return queryset
        return queryset.filter(
            Q(email__iexact=user.email)
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

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def accept(self, request):
        serializer = OrganizationInvitationAcceptSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        invitation, membership = serializer.save()
        return Response(
            {
                "invitation": OrganizationInvitationSerializer(invitation).data,
                "membership": OrganizationMembershipSerializer(membership).data,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def revoke(self, request, pk=None):
        invitation = self.get_object()
        if invitation.status != OrganizationInvitation.Statuses.PENDING:
            return Response({"detail": "Only pending invitations can be revoked."}, status=status.HTTP_400_BAD_REQUEST)
        if not user_can_manage_organization(request.user, invitation.organization):
            return Response({"detail": "You cannot manage this organization."}, status=status.HTTP_403_FORBIDDEN)
        invitation.status = OrganizationInvitation.Statuses.REVOKED
        invitation.revoked_by_user = request.user
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["status", "revoked_by_user", "revoked_at", "updated_at"])
        return Response({"invitation": OrganizationInvitationSerializer(invitation).data})
