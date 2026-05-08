from rest_framework import serializers

from apps.cases.access import get_active_membership, user_can_access_case
from apps.cases.models import Case
from apps.organizations.models import OrganizationMembership
from apps.organizations.services import get_or_create_personal_organization

from .models import Conversation, ConversationParticipant, ConversationPost


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    organization_id = serializers.IntegerField(source="organization.id", read_only=True, allow_null=True)
    membership_id = serializers.IntegerField(source="membership.id", read_only=True, allow_null=True)

    class Meta:
        model = ConversationParticipant
        fields = (
            "id",
            "user_id",
            "organization_id",
            "membership_id",
            "role",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(source="case.id", read_only=True, allow_null=True)
    case_share_request_id = serializers.IntegerField(source="case_share_request.id", read_only=True, allow_null=True)
    created_by_user_id = serializers.IntegerField(source="created_by_user.id", read_only=True, allow_null=True)
    participants = ConversationParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "subject",
            "case_id",
            "case_share_request_id",
            "created_by_user_id",
            "status",
            "metadata_json",
            "participants",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ConversationCreateSerializer(serializers.ModelSerializer):
    case_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Conversation
        fields = ("subject", "case_id", "metadata_json")
        extra_kwargs = {"metadata_json": {"required": False}}

    def validate_case_id(self, value):
        if value is None:
            return value
        request = self.context["request"]
        try:
            case = Case.objects.select_related("owner_organization").get(id=value)
        except Case.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid case.") from exc
        if not user_can_access_case(request.user, case):
            raise serializers.ValidationError("You do not have access to this case.")
        self.context["case"] = case
        return value

    def create(self, validated_data):
        request = self.context["request"]
        case = self.context.get("case")
        validated_data.pop("case_id", None)
        conversation = Conversation.objects.create(
            case=case,
            created_by_user=request.user,
            **validated_data,
        )
        organization = case.owner_organization if case is not None else get_or_create_personal_organization(request.user)
        membership = get_active_membership(request.user, organization)
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user,
            organization=organization,
            membership=membership,
            role=ConversationParticipant.Roles.OWNER,
            status=ConversationParticipant.Statuses.ACTIVE,
        )
        return conversation


class ConversationPostSerializer(serializers.ModelSerializer):
    conversation_id = serializers.IntegerField(source="conversation.id", read_only=True)
    author_user_id = serializers.IntegerField(source="author_user.id", read_only=True)
    author_membership_id = serializers.IntegerField(source="author_membership.id", read_only=True, allow_null=True)

    class Meta:
        model = ConversationPost
        fields = (
            "id",
            "conversation_id",
            "author_user_id",
            "author_membership_id",
            "body",
            "metadata_json",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ConversationPostCreateSerializer(serializers.ModelSerializer):
    author_membership_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = ConversationPost
        fields = ("body", "metadata_json", "author_membership_id")
        extra_kwargs = {"metadata_json": {"required": False}}

    def validate_author_membership_id(self, value):
        if value is None:
            return value
        request = self.context["request"]
        try:
            membership = OrganizationMembership.objects.get(
                id=value,
                user=request.user,
                status=OrganizationMembership.Statuses.ACTIVE,
            )
        except OrganizationMembership.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid membership.") from exc
        self.context["author_membership"] = membership
        return value

    def validate(self, attrs):
        conversation = self.context["conversation"]
        request = self.context["request"]
        if conversation.status != Conversation.Statuses.ACTIVE:
            raise serializers.ValidationError({"conversation": "Cannot post to a closed conversation."})

        membership = self.context.get("author_membership")
        participant_queryset = ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user,
            status=ConversationParticipant.Statuses.ACTIVE,
        )
        if membership is not None:
            participant_queryset = participant_queryset.filter(membership=membership)
        if not participant_queryset.exists():
            raise serializers.ValidationError({"conversation": "You are not an active participant."})
        if membership is None:
            participant = participant_queryset.select_related("membership").first()
            self.context["author_membership"] = participant.membership if participant is not None else None
        return attrs

    def create(self, validated_data):
        conversation = self.context["conversation"]
        request = self.context["request"]
        validated_data.pop("author_membership_id", None)
        post = ConversationPost.objects.create(
            conversation=conversation,
            author_user=request.user,
            author_membership=self.context.get("author_membership"),
            **validated_data,
        )
        conversation.save(update_fields=["updated_at"])
        return post

