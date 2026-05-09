from django.conf import settings
from django.db import transaction

from apps.organizations.models import OrganizationMembership

from .models import Notification


def _case_share_request_recipient_users(share_request):
    if share_request.recipient_membership_id:
        return [share_request.recipient_membership.user]

    return [
        membership.user
        for membership in OrganizationMembership.objects.select_related("user").filter(
            organization=share_request.recipient_organization,
            status=OrganizationMembership.Statuses.ACTIVE,
            scope=OrganizationMembership.Scopes.ORGANIZATION,
            role__in={
                OrganizationMembership.Roles.OWNER,
                OrganizationMembership.Roles.ADMIN,
                OrganizationMembership.Roles.ADMINISTRATIVE,
            },
        )
    ]


def create_notification(
    *,
    recipient_user=None,
    recipient_user_id=None,
    notification_type,
    title,
    body="",
    actor_user=None,
    priority=Notification.Priorities.NORMAL,
    target_type="",
    target_id="",
    deep_link="",
    metadata_json=None,
    skip_actor=True,
):
    if recipient_user is None and recipient_user_id is None:
        return None
    if recipient_user_id is None:
        recipient_user_id = recipient_user.id
    if skip_actor and actor_user is not None and recipient_user_id == actor_user.id:
        return None

    notification = Notification.objects.create(
        recipient_user_id=recipient_user_id,
        actor_user=actor_user,
        notification_type=notification_type,
        title=title,
        body=body,
        priority=priority,
        target_type=target_type,
        target_id=str(target_id) if target_id else "",
        deep_link=deep_link,
        metadata_json=metadata_json or {},
    )

    if getattr(settings, "NOTIFICATIONS_PUSH_DELIVERY_ENABLED", False):
        from .tasks import deliver_notification_pushes_task

        transaction.on_commit(lambda: deliver_notification_pushes_task.delay(notification.id))

    return notification


def notify_case_share_request_created(share_request, *, actor_user):
    notifications = []
    for user in _case_share_request_recipient_users(share_request):
        notification = create_notification(
            recipient_user=user,
            actor_user=actor_user,
            notification_type=Notification.Types.CASE_SHARE_REQUEST_CREATED,
            title="Nuova richiesta di condivisione",
            body="Una pratica è stata condivisa con la tua organizzazione.",
            priority=Notification.Priorities.HIGH,
            target_type="case_share_request",
            target_id=share_request.id,
            deep_link=f"elettra://case-share-requests/{share_request.id}",
            metadata_json={
                "case_id": share_request.case_id,
                "recipient_organization_id": share_request.recipient_organization_id,
                "share_scope": share_request.share_scope,
            },
        )
        if notification is not None:
            notifications.append(notification)
    return notifications


def notify_case_share_request_revoked(share_request, *, actor_user):
    notifications = []
    for user in _case_share_request_recipient_users(share_request):
        notification = create_notification(
            recipient_user=user,
            actor_user=actor_user,
            notification_type=Notification.Types.CASE_SHARE_REQUEST_REVOKED,
            title="Condivisione revocata",
            body="La condivisione di una pratica è stata revocata.",
            target_type="case_share_request",
            target_id=share_request.id,
            deep_link=f"elettra://case-share-requests/{share_request.id}",
            metadata_json={
                "case_id": share_request.case_id,
                "status": share_request.status,
                "recipient_organization_id": share_request.recipient_organization_id,
            },
        )
        if notification is not None:
            notifications.append(notification)
    return notifications


def notify_case_share_request_status_changed(share_request, *, actor_user, notification_type, title, body):
    return create_notification(
        recipient_user=share_request.requester_user,
        actor_user=actor_user,
        notification_type=notification_type,
        title=title,
        body=body,
        target_type="case_share_request",
        target_id=share_request.id,
        deep_link=f"elettra://case-share-requests/{share_request.id}",
        metadata_json={
            "case_id": share_request.case_id,
            "status": share_request.status,
            "recipient_organization_id": share_request.recipient_organization_id,
        },
    )


def notify_conversation_post_created(post):
    participant_users = (
        post.conversation.participants.select_related("user")
        .filter(status="active", user__is_active=True)
        .exclude(user=post.author_user)
        .values_list("user_id", flat=True)
        .distinct()
    )
    notifications = []
    for user_id in participant_users:
        notification = create_notification(
            recipient_user_id=user_id,
            actor_user=post.author_user,
            notification_type=Notification.Types.CONVERSATION_POST_CREATED,
            title="Nuovo messaggio",
            body="Hai un nuovo messaggio in una conversazione.",
            target_type="conversation",
            target_id=post.conversation_id,
            deep_link=f"elettra://conversations/{post.conversation_id}",
            metadata_json={
                "conversation_id": post.conversation_id,
                "post_id": post.id,
                "case_id": post.conversation.case_id,
            },
        )
        if notification is not None:
            notifications.append(notification)
    return notifications
