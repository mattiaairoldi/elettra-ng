from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from .context import estimate_cost, estimate_token_count
from .models import AiMessage, AiSession, AiUsageLedger


class AiUsageLimitExceeded(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def _positive_int_setting(name: str, default: int = 0) -> int:
    value = int(getattr(settings, name, default))
    return max(value, 0)


def _positive_decimal_setting(name: str, default: Decimal | int = 0) -> Decimal:
    value = Decimal(str(getattr(settings, name, default)))
    return max(value, Decimal("0"))


def get_session_organization(session: AiSession):
    if session.case_id is None:
        return None
    return session.case.owner_organization


def get_ai_provider_model_name(provider) -> str:
    return str(getattr(provider, "model", "") or "")


def get_daily_message_count(user) -> int:
    return AiMessage.objects.filter(
        session__user=user,
        role=AiMessage.Roles.USER,
        created_at__date=timezone.localdate(),
    ).count()


def get_case_diagnostic_turn_count(case) -> int:
    if case is None:
        return 0
    return AiMessage.objects.filter(
        session__case=case,
        role=AiMessage.Roles.USER,
        metadata_json__diagnostic__kind="user_observation",
    ).count()


def _totals(queryset) -> dict:
    aggregated = queryset.aggregate(
        total_tokens=Sum("total_tokens"),
        estimated_cost=Sum("estimated_cost"),
    )
    return {
        "total_tokens": int(aggregated["total_tokens"] or 0),
        "estimated_cost": aggregated["estimated_cost"] or Decimal("0"),
    }


def get_daily_user_usage_totals(user) -> dict:
    return _totals(
        AiUsageLedger.objects.filter(
            user=user,
            created_at__date=timezone.localdate(),
        )
    )


def get_monthly_organization_usage_totals(organization) -> dict:
    if organization is None:
        return {"total_tokens": 0, "estimated_cost": Decimal("0")}

    today = timezone.localdate()
    return _totals(
        AiUsageLedger.objects.filter(
            organization=organization,
            created_at__date__gte=today.replace(day=1),
        )
    )


def enforce_ai_usage_limits(
    session: AiSession,
    purpose: str,
    estimated_input_tokens: int = 0,
    estimated_output_tokens: int = 0,
    check_case_turn_limit: bool = False,
) -> None:
    daily_token_limit = _positive_int_setting("AI_DAILY_TOKEN_LIMIT_PER_USER", 20000)
    daily_cost_limit = _positive_decimal_setting("AI_DAILY_ESTIMATED_COST_LIMIT_PER_USER", 0)
    organization_monthly_cost_limit = _positive_decimal_setting(
        "AI_MONTHLY_ESTIMATED_COST_LIMIT_PER_ORGANIZATION",
        0,
    )
    case_diagnostic_turn_limit = _positive_int_setting("AI_CASE_DIAGNOSTIC_TURN_LIMIT", 8)

    if check_case_turn_limit and case_diagnostic_turn_limit > 0:
        used_turns = get_case_diagnostic_turn_count(session.case)
        if used_turns >= case_diagnostic_turn_limit:
            raise AiUsageLimitExceeded(
                "Case AI diagnostic turn limit reached.",
                code="case_diagnostic_turn_limit_reached",
            )

    daily_totals = get_daily_user_usage_totals(session.user)
    estimated_tokens = max(estimated_input_tokens, 0) + max(estimated_output_tokens, 0)
    if daily_token_limit > 0 and daily_totals["total_tokens"] + estimated_tokens > daily_token_limit:
        raise AiUsageLimitExceeded(
            "Daily AI token limit reached.",
            code="daily_token_limit_reached",
        )

    estimated_request_cost = estimate_cost(
        max(estimated_input_tokens, 0),
        max(estimated_output_tokens, 0),
    )
    if daily_cost_limit > 0 and daily_totals["estimated_cost"] + estimated_request_cost > daily_cost_limit:
        raise AiUsageLimitExceeded(
            "Daily AI cost limit reached.",
            code="daily_cost_limit_reached",
        )

    organization = get_session_organization(session)
    organization_totals = get_monthly_organization_usage_totals(organization)
    if (
        organization_monthly_cost_limit > 0
        and organization_totals["estimated_cost"] + estimated_request_cost > organization_monthly_cost_limit
    ):
        raise AiUsageLimitExceeded(
            "Organization monthly AI cost limit reached.",
            code="organization_monthly_cost_limit_reached",
        )


def record_ai_usage(
    *,
    session: AiSession,
    message: AiMessage | None,
    purpose: str,
    provider,
    input_payload,
    output_payload,
    metadata: dict | None = None,
) -> AiUsageLedger:
    input_tokens = estimate_token_count(input_payload)
    output_tokens = estimate_token_count(output_payload)
    return AiUsageLedger.objects.create(
        session=session,
        message=message,
        user=session.user,
        organization=get_session_organization(session),
        case=session.case,
        purpose=purpose,
        provider=getattr(provider, "provider_name", "") or "",
        model_name=get_ai_provider_model_name(provider),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        estimated_cost=estimate_cost(input_tokens, output_tokens),
        metadata_json=metadata or {},
    )


def build_ai_usage_summary(session: AiSession) -> dict:
    organization = get_session_organization(session)
    daily_totals = get_daily_user_usage_totals(session.user)
    organization_totals = get_monthly_organization_usage_totals(organization)

    return {
        "daily_user": {
            "messages_used": get_daily_message_count(session.user),
            "message_limit": _positive_int_setting("AI_DAILY_MESSAGE_LIMIT_PER_USER", 20),
            "tokens_used": daily_totals["total_tokens"],
            "token_limit": _positive_int_setting("AI_DAILY_TOKEN_LIMIT_PER_USER", 20000),
            "estimated_cost": str(daily_totals["estimated_cost"]),
            "estimated_cost_limit": str(
                _positive_decimal_setting("AI_DAILY_ESTIMATED_COST_LIMIT_PER_USER", 0)
            ),
        },
        "case": {
            "diagnostic_turns_used": get_case_diagnostic_turn_count(session.case),
            "diagnostic_turn_limit": _positive_int_setting("AI_CASE_DIAGNOSTIC_TURN_LIMIT", 8),
        },
        "organization_monthly": {
            "organization_id": organization.id if organization is not None else None,
            "tokens_used": organization_totals["total_tokens"],
            "estimated_cost": str(organization_totals["estimated_cost"]),
            "estimated_cost_limit": str(
                _positive_decimal_setting("AI_MONTHLY_ESTIMATED_COST_LIMIT_PER_ORGANIZATION", 0)
            ),
        },
    }
