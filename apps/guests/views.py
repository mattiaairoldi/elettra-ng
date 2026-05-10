from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_assistant.diagnostics import build_diagnostic_selection_metadata
from apps.ai_assistant.models import AiDiagnosticSnapshot, AiMessage, AiSession
from apps.ai_assistant.serializers import AiDiagnosticSnapshotSerializer, AiMessageSerializer
from apps.cases.serializers import CaseSerializer
from apps.identity.jwt import build_token_payload, record_token_login
from apps.identity.serializers import UserSerializer, raise_serializer_validation_error
from apps.identity.tasks import send_verification_email_task
from apps.ai_assistant.tasks import generate_ai_diagnostic_reply_task
from apps.troubleshooting.models import DiagnosticAdviceStep, DiagnosticChapter
from apps.troubleshooting.serializers import DiagnosticAdviceStepSerializer

from .serializers import (
    GuestDiagnosticTurnResponseSerializer,
    GuestDiagnosticTurnSerializer,
    GuestPromotionResponseSerializer,
    GuestPromotionSerializer,
    GuestSessionResponseSerializer,
)
from .services import (
    authenticate_guest_session,
    build_guest_quotas,
    create_guest_session,
    promote_guest_session,
)


def serialize_guest_session(session, token: str | None = None) -> dict:
    payload = {
        "guest_session_id": session.public_id,
        "status": session.status,
        "expires_at": session.expires_at,
        "quotas": build_guest_quotas(session),
    }
    if token is not None:
        payload["guest_token"] = token
    return payload


def serialize_guest_promotion(promotion: dict) -> dict:
    session = promotion["guest_session"]
    user = promotion["user"]
    record_token_login(user)
    payload = {
        "user": UserSerializer(user).data,
        "tokens": build_token_payload(user),
        "guest_session": serialize_guest_session(session),
        "case": CaseSerializer(promotion["case"]).data,
        "diagnostic_snapshot": None,
    }
    snapshot = promotion.get("diagnostic_snapshot")
    if snapshot is not None:
        payload["diagnostic_snapshot"] = AiDiagnosticSnapshotSerializer(snapshot).data
    return payload


def get_or_create_ai_session(guest_session):
    session = guest_session.ai_sessions.filter(status=AiSession.Statuses.ACTIVE).first()
    if session is not None:
        return session
    return AiSession.objects.create(guest_session=guest_session)


def get_guest_ai_session(guest_session):
    session = guest_session.ai_sessions.filter(status=AiSession.Statuses.ACTIVE).first()
    if session is None:
        raise NotFound("Guest AI session not found.")
    return session


def get_advice_steps(chapter, option):
    if chapter is None:
        return []

    queryset = DiagnosticAdviceStep.objects.filter(
        chapter=chapter,
        chapter__is_public=True,
        chapter__status=DiagnosticChapter.Statuses.PUBLISHED,
        is_active=True,
    ).select_related("chapter", "chapter_option")
    if option is not None:
        queryset = queryset.filter(Q(chapter_option=option) | Q(chapter_option__isnull=True))
    else:
        queryset = queryset.filter(chapter_option__isnull=True)
    return list(queryset[:3])


def build_guest_call_to_action(code: str, title: str, message: str) -> dict:
    return {
        "code": code,
        "title": title,
        "message": message,
        "action_label": "Accedi per salvare",
    }


def can_use_ai(quotas: dict) -> bool:
    return quotas["ai_turns_remaining"] > 0 and quotas["messages_remaining"] >= 2


class GuestSessionCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=None, responses={201: GuestSessionResponseSerializer})
    def post(self, request):
        session, token = create_guest_session(request)
        return Response(serialize_guest_session(session, token), status=status.HTTP_201_CREATED)


class GuestSessionCurrentView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: GuestSessionResponseSerializer})
    def get(self, request):
        session = authenticate_guest_session(request)
        return Response(serialize_guest_session(session))


class GuestPromotionView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=GuestPromotionSerializer,
        responses={201: GuestPromotionResponseSerializer},
    )
    def post(self, request):
        guest_session = authenticate_guest_session(request)
        serializer = GuestPromotionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            promotion = promote_guest_session(guest_session, serializer.validated_data)
        except DjangoValidationError as exc:
            raise_serializer_validation_error(exc)
        send_verification_email_task.delay(promotion["user"].id)
        return Response(serialize_guest_promotion(promotion), status=status.HTTP_201_CREATED)


class GuestDiagnosticTurnView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=GuestDiagnosticTurnSerializer,
        responses={200: GuestDiagnosticTurnResponseSerializer},
    )
    def post(self, request):
        guest_session = authenticate_guest_session(request)
        serializer = GuestDiagnosticTurnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chapter = serializer.context.get("diagnostic_chapter")
        option = serializer.context.get("diagnostic_chapter_option")
        advice_steps = get_advice_steps(chapter, option)
        ai_session = get_or_create_ai_session(guest_session)
        quotas = build_guest_quotas(guest_session)
        use_ai = serializer.validated_data.get("use_ai", True)
        call_to_action = {}
        user_message = None
        assistant_message = None

        if use_ai and can_use_ai(quotas):
            diagnostic_metadata = build_diagnostic_selection_metadata(chapter, option)
            user_message = AiMessage.objects.create(
                session=ai_session,
                role=AiMessage.Roles.USER,
                content=serializer.validated_data["message"].strip(),
                metadata_json={"diagnostic": {**diagnostic_metadata, "guest": True}},
            )
            assistant_message = AiMessage.objects.create(
                session=ai_session,
                role=AiMessage.Roles.ASSISTANT,
                content="",
                status=AiMessage.Statuses.QUEUED,
                metadata_json={"diagnostic": {"status": "queued", "guest": True}},
            )
            generate_ai_diagnostic_reply_task.delay(assistant_message.id)
            assistant_message.refresh_from_db()
        elif use_ai:
            call_to_action = build_guest_call_to_action(
                "guest_ai_limit_reached",
                "Limite ospite raggiunto",
                "Per continuare la diagnosi e salvare lo storico serve accedere o creare un account.",
            )
        else:
            call_to_action = build_guest_call_to_action(
                "guest_saved_advice_only",
                "Percorso non salvato",
                "I consigli sono disponibili subito. Accedi per salvare una pratica completa.",
            )

        try:
            snapshot = ai_session.diagnostic_snapshot
        except AiDiagnosticSnapshot.DoesNotExist:
            snapshot_data = None
        else:
            snapshot_data = AiDiagnosticSnapshotSerializer(snapshot).data

        quotas = build_guest_quotas(guest_session)
        if not call_to_action and quotas["ai_turns_remaining"] == 0:
            call_to_action = build_guest_call_to_action(
                "guest_ai_limit_reached",
                "Limite ospite raggiunto",
                "Hai usato i turni AI disponibili come ospite. Accedi per trasformare il riepilogo in una pratica.",
            )

        return Response(
            {
                "advice_steps": DiagnosticAdviceStepSerializer(advice_steps, many=True).data,
                "user_message": AiMessageSerializer(user_message).data if user_message is not None else None,
                "assistant_message": (
                    AiMessageSerializer(assistant_message).data if assistant_message is not None else None
                ),
                "diagnostic_snapshot": snapshot_data,
                "quotas": quotas,
                "call_to_action": call_to_action,
            }
        )


class GuestMessageDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: AiMessageSerializer})
    def get(self, request, message_id):
        guest_session = authenticate_guest_session(request)
        ai_session = get_guest_ai_session(guest_session)
        try:
            message = ai_session.messages.get(id=message_id)
        except AiMessage.DoesNotExist as exc:
            raise NotFound("Message not found.") from exc
        return Response(AiMessageSerializer(message).data)


class GuestDiagnosticSnapshotView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: AiDiagnosticSnapshotSerializer})
    def get(self, request):
        guest_session = authenticate_guest_session(request)
        ai_session = get_guest_ai_session(guest_session)
        try:
            snapshot = ai_session.diagnostic_snapshot
        except AiDiagnosticSnapshot.DoesNotExist as exc:
            raise NotFound("Diagnostic snapshot not found.") from exc
        return Response(AiDiagnosticSnapshotSerializer(snapshot).data)
