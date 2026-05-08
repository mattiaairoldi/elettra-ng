from django.db import transaction
from django.utils import timezone

from apps.conversations.models import Conversation, ConversationParticipant
from apps.organizations.services import get_or_create_personal_organization

from .access import get_active_membership
from .events import create_case_event, update_case_status
from .models import Case, CaseEvent, CaseShareRequest


def _add_participant(conversation, user, organization=None, membership=None, role=ConversationParticipant.Roles.PARTICIPANT):
    return ConversationParticipant.objects.get_or_create(
        conversation=conversation,
        user=user,
        organization=organization,
        defaults={
            "membership": membership,
            "role": role,
            "status": ConversationParticipant.Statuses.ACTIVE,
        },
    )[0]


def create_conversation_for_share_request(share_request, actor_user):
    if hasattr(share_request, "conversation"):
        return share_request.conversation

    conversation = Conversation.objects.create(
        subject=share_request.visible_title,
        case=share_request.case,
        case_share_request=share_request,
        created_by_user=actor_user,
        metadata_json={"source": "case_share_request"},
    )
    requester_organization = share_request.case.owner_organization
    requester_membership = get_active_membership(share_request.requester_user, requester_organization)
    _add_participant(
        conversation=conversation,
        user=share_request.requester_user,
        organization=requester_organization,
        membership=requester_membership,
        role=ConversationParticipant.Roles.OWNER,
    )

    recipient_membership = share_request.recipient_membership or get_active_membership(
        actor_user,
        share_request.recipient_organization,
    )
    _add_participant(
        conversation=conversation,
        user=actor_user,
        organization=share_request.recipient_organization,
        membership=recipient_membership,
    )
    return conversation


@transaction.atomic
def accept_case_share_request(share_request, actor_user):
    share_request.status = CaseShareRequest.Statuses.ACCEPTED
    share_request.accepted_by_user = actor_user
    share_request.accepted_at = timezone.now()
    share_request.save(update_fields=["status", "accepted_by_user", "accepted_at", "updated_at"])

    conversation = create_conversation_for_share_request(share_request, actor_user)
    if share_request.case.status in {Case.Statuses.OPEN, Case.Statuses.IN_DIAGNOSIS}:
        update_case_status(
            share_request.case,
            Case.Statuses.WAITING_PROFESSIONAL,
            actor_user=actor_user,
            payload={"reason": "case_share_request_accepted", "share_request_id": share_request.id},
        )

    create_case_event(
        case=share_request.case,
        event_type=CaseEvent.EventTypes.CASE_SHARE_REQUEST_ACCEPTED,
        actor_user=actor_user,
        payload={"share_request_id": share_request.id, "conversation_id": conversation.id},
    )
    return conversation


@transaction.atomic
def reject_case_share_request(share_request, actor_user, reason=""):
    share_request.status = CaseShareRequest.Statuses.REJECTED
    share_request.rejected_by_user = actor_user
    share_request.rejected_at = timezone.now()
    share_request.rejection_reason = reason
    share_request.save(update_fields=["status", "rejected_by_user", "rejected_at", "rejection_reason", "updated_at"])
    create_case_event(
        case=share_request.case,
        event_type=CaseEvent.EventTypes.CASE_SHARE_REQUEST_REJECTED,
        actor_user=actor_user,
        payload={"share_request_id": share_request.id, "reason_provided": bool(reason)},
    )


@transaction.atomic
def revoke_case_share_request(share_request, actor_user):
    share_request.status = CaseShareRequest.Statuses.REVOKED
    share_request.revoked_by_user = actor_user
    share_request.revoked_at = timezone.now()
    share_request.save(update_fields=["status", "revoked_by_user", "revoked_at", "updated_at"])
    create_case_event(
        case=share_request.case,
        event_type=CaseEvent.EventTypes.CASE_SHARE_REQUEST_REVOKED,
        actor_user=actor_user,
        payload={"share_request_id": share_request.id},
    )


def ensure_personal_case_owner(case):
    if case.owner_organization_id:
        return case.owner_organization
    return get_or_create_personal_organization(case.customer_user)

