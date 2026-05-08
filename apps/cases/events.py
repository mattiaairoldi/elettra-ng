from django.utils import timezone

from .models import Case, CaseEvent


TERMINAL_CASE_STATUSES = {
    Case.Statuses.RESOLVED,
    Case.Statuses.CLOSED,
    Case.Statuses.CANCELLED,
}


def create_case_event(case, event_type, actor_user=None, payload=None):
    return CaseEvent.objects.create(
        case=case,
        event_type=event_type,
        actor_user=actor_user,
        payload_json=payload or {},
    )


def update_case_status(case, new_status, actor_user=None, payload=None):
    previous_status = case.status
    case.status = new_status
    case.closed_at = timezone.now() if new_status in TERMINAL_CASE_STATUSES else None
    case.save(update_fields=["status", "closed_at", "updated_at"])
    create_case_event(
        case=case,
        event_type=CaseEvent.EventTypes.STATUS_CHANGED,
        actor_user=actor_user,
        payload={
            "previous_status": previous_status,
            "status": new_status,
            **(payload or {}),
        },
    )
    return case
