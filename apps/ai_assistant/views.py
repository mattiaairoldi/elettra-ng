import json
import time

from django.conf import settings
from django.http import StreamingHttpResponse
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, OpenApiTypes, extend_schema, inline_serializer
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .context import compact_ai_context
from .models import AiDiagnosticSnapshot, AiMessage, AiSession
from .provider import build_diagnostic_context
from .serializers import (
    AiContextCompactSerializer,
    AiContextDigestSerializer,
    AiDiagnosticSnapshotSerializer,
    AiDiagnosticTurnCreateSerializer,
    AiMessageCreateSerializer,
    AiMessagesQuerySerializer,
    AiMessageSerializer,
    AiSessionCreateSerializer,
    AiSessionSerializer,
)
from .tasks import generate_ai_diagnostic_reply_task, generate_ai_reply_task


def build_ai_session_queryset(user):
    queryset = AiSession.objects.select_related(
        "user",
        "case",
        "case__category",
        "case__assigned_professional",
        "case__current_diagnostic_node",
    ).prefetch_related("messages")
    if user.role == "admin":
        return queryset
    return queryset.filter(user=user)


def build_sse_event(event_name, payload):
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"


class AiSessionViewSet(GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = AiSession.objects.all()

    def get_queryset(self):
        return build_ai_session_queryset(self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return AiSessionCreateSerializer
        return AiSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session, created = serializer.create_or_reuse()
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(AiSessionSerializer(session).data, status=response_status)

    def retrieve(self, request, *args, **kwargs):
        session = self.get_object()
        return Response(AiSessionSerializer(session).data)

    @extend_schema(
        parameters=[
            OpenApiParameter("after_id", OpenApiTypes.INT, OpenApiParameter.QUERY),
            OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
        ],
        responses={200: AiMessageSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated], url_path="messages")
    def messages(self, request, pk=None):
        session = self.get_object()
        query_serializer = AiMessagesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        queryset = session.messages.all()
        after_id = query_serializer.validated_data.get("after_id")
        if after_id is not None:
            queryset = queryset.filter(id__gt=after_id)
        limit = query_serializer.validated_data.get("limit")
        if limit is not None:
            queryset = queryset[:limit]
        serializer = AiMessageSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path=r"messages/(?P<message_id>\d+)",
    )
    @extend_schema(
        operation_id="ai_sessions_message_retrieve",
        parameters=[OpenApiParameter("message_id", OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: AiMessageSerializer},
    )
    def message_detail(self, request, pk=None, message_id=None):
        session = self.get_object()
        try:
            message = session.messages.get(id=message_id)
        except AiMessage.DoesNotExist as exc:
            raise NotFound("Message not found.") from exc
        return Response(AiMessageSerializer(message).data)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path=r"messages/(?P<message_id>\d+)/stream",
    )
    @extend_schema(
        operation_id="ai_sessions_message_stream",
        parameters=[OpenApiParameter("message_id", OpenApiTypes.INT, OpenApiParameter.PATH)],
        responses={200: OpenApiResponse(description="Server-sent events stream for an assistant message.")},
    )
    def message_stream(self, request, pk=None, message_id=None):
        session = self.get_object()
        try:
            message = session.messages.get(id=message_id)
        except AiMessage.DoesNotExist as exc:
            raise NotFound("Message not found.") from exc
        if message.role != AiMessage.Roles.ASSISTANT:
            raise ParseError("Streaming is available only for assistant messages.")

        poll_interval = max(float(getattr(settings, "AI_STREAM_POLL_INTERVAL_SECONDS", 0.5)), 0.0)
        timeout_seconds = max(float(getattr(settings, "AI_STREAM_TIMEOUT_SECONDS", 30.0)), 0.0)

        def event_stream():
            started_at = time.monotonic()
            last_status = None
            last_content = None
            while True:
                message.refresh_from_db()
                serialized = AiMessageSerializer(message).data
                current_content = serialized["content"] or ""
                previous_content = last_content or ""
                if previous_content and current_content.startswith(previous_content):
                    delta = current_content[len(previous_content) :]
                    if delta:
                        yield build_sse_event(
                            "delta",
                            {
                                "message_id": message.id,
                                "delta": delta,
                                "status": serialized["status"],
                            },
                        )
                if serialized["status"] != last_status or serialized["content"] != last_content:
                    yield build_sse_event("message", serialized)
                    last_status = serialized["status"]
                    last_content = serialized["content"]

                if message.status in {AiMessage.Statuses.COMPLETED, AiMessage.Statuses.FAILED}:
                    yield build_sse_event("done", {"message_id": message.id, "status": message.status})
                    break

                elapsed = time.monotonic() - started_at
                if elapsed >= timeout_seconds:
                    yield build_sse_event("timeout", {"message_id": message.id, "status": message.status})
                    break

                time.sleep(poll_interval)
                yield ": heartbeat\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @extend_schema(operation_id="ai_sessions_status_retrieve", responses={200: AiSessionSerializer})
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated], url_path="status")
    def status_snapshot(self, request, pk=None):
        session = self.get_object()
        return Response(AiSessionSerializer(session).data)

    @extend_schema(
        operation_id="ai_sessions_diagnostic_context_retrieve",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated], url_path="context")
    def diagnostic_context(self, request, pk=None):
        session = self.get_object()
        return Response(build_diagnostic_context(session))

    @extend_schema(
        operation_id="ai_sessions_context_digest_list",
        responses={200: AiContextDigestSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated], url_path="context-digests")
    def context_digests(self, request, pk=None):
        session = self.get_object()
        serializer = AiContextDigestSerializer(session.context_digests.all(), many=True)
        return Response(serializer.data)

    @extend_schema(
        operation_id="ai_sessions_context_compact",
        request=AiContextCompactSerializer,
        responses={
            200: inline_serializer(
                name="AiContextCompactResponse",
                fields={"context_digest": AiContextDigestSerializer(allow_null=True)},
            )
        },
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated], url_path="compact-context")
    def compact_context(self, request, pk=None):
        session = self.get_object()
        serializer = AiContextCompactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        digest = compact_ai_context(
            session,
            trigger_reason="manual",
            force=serializer.validated_data["force"],
        )
        return Response(
            {
                "context_digest": AiContextDigestSerializer(digest).data if digest is not None else None,
            }
        )

    @extend_schema(
        operation_id="ai_sessions_diagnostic_snapshot_retrieve",
        responses={200: AiDiagnosticSnapshotSerializer},
    )
    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="diagnostic-snapshot",
    )
    def diagnostic_snapshot(self, request, pk=None):
        session = self.get_object()
        try:
            snapshot = session.diagnostic_snapshot
        except AiDiagnosticSnapshot.DoesNotExist as exc:
            raise NotFound("Diagnostic snapshot not found.") from exc
        return Response(AiDiagnosticSnapshotSerializer(snapshot).data)

    @messages.mapping.post
    @extend_schema(
        operation_id="ai_sessions_message_create",
        request=AiMessageCreateSerializer,
        responses={
            202: inline_serializer(
                name="AiMessageCreateResponse",
                fields={
                    "user_message": AiMessageSerializer(),
                    "assistant_message": AiMessageSerializer(),
                },
            )
        },
    )
    def create_message(self, request, pk=None):
        session = self.get_object()
        serializer = AiMessageCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "session": session,
                "daily_limit": getattr(settings, "AI_DAILY_MESSAGE_LIMIT_PER_USER", 20),
            },
        )
        serializer.is_valid(raise_exception=True)

        user_message = AiMessage.objects.create(
            session=session,
            role=AiMessage.Roles.USER,
            content=serializer.validated_data["content"],
        )
        assistant_message = AiMessage.objects.create(
            session=session,
            role=AiMessage.Roles.ASSISTANT,
            content="",
            status=AiMessage.Statuses.QUEUED,
        )
        generate_ai_reply_task.delay(assistant_message.id)
        assistant_message.refresh_from_db()
        return Response(
            {
                "user_message": AiMessageSerializer(user_message).data,
                "assistant_message": AiMessageSerializer(assistant_message).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        operation_id="ai_sessions_diagnostic_turn_create",
        request=AiDiagnosticTurnCreateSerializer,
        responses={
            202: inline_serializer(
                name="AiDiagnosticTurnCreateResponse",
                fields={
                    "user_message": AiMessageSerializer(),
                    "assistant_message": AiMessageSerializer(),
                    "diagnostic_snapshot": AiDiagnosticSnapshotSerializer(allow_null=True),
                },
            )
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="diagnostic-turns",
    )
    def diagnostic_turns(self, request, pk=None):
        session = self.get_object()
        serializer = AiDiagnosticTurnCreateSerializer(
            data=request.data,
            context={
                "request": request,
                "session": session,
                "daily_limit": getattr(settings, "AI_DAILY_MESSAGE_LIMIT_PER_USER", 20),
            },
        )
        serializer.is_valid(raise_exception=True)
        diagnostic_chapter = serializer.context.get("diagnostic_chapter")
        diagnostic_chapter_option = serializer.context.get("diagnostic_chapter_option")
        diagnostic_metadata = {"kind": "user_observation"}
        if diagnostic_chapter is not None:
            diagnostic_metadata.update(
                {
                    "diagnostic_chapter_id": diagnostic_chapter.id,
                    "diagnostic_chapter_name": diagnostic_chapter.name,
                    "diagnostic_chapter_slug": diagnostic_chapter.slug,
                    "diagnostic_chapter_prompt_context": diagnostic_chapter.prompt_context,
                    "diagnostic_chapter_safety_context": diagnostic_chapter.safety_context,
                }
            )
        if diagnostic_chapter_option is not None:
            diagnostic_metadata.update(
                {
                    "diagnostic_chapter_option_id": diagnostic_chapter_option.id,
                    "diagnostic_chapter_option_label": diagnostic_chapter_option.label,
                    "diagnostic_chapter_option_slug": diagnostic_chapter_option.slug,
                    "diagnostic_chapter_option_type": diagnostic_chapter_option.option_type,
                    "diagnostic_chapter_option_prompt_hint": diagnostic_chapter_option.prompt_hint,
                }
            )

        user_message = AiMessage.objects.create(
            session=session,
            role=AiMessage.Roles.USER,
            content=serializer.validated_data["content"],
            metadata_json={"diagnostic": diagnostic_metadata},
        )
        assistant_message = AiMessage.objects.create(
            session=session,
            role=AiMessage.Roles.ASSISTANT,
            content="",
            status=AiMessage.Statuses.QUEUED,
            metadata_json={"diagnostic": {"status": "queued"}},
        )
        generate_ai_diagnostic_reply_task.delay(assistant_message.id)
        assistant_message.refresh_from_db()

        try:
            snapshot = session.diagnostic_snapshot
        except AiDiagnosticSnapshot.DoesNotExist:
            snapshot_data = None
        else:
            snapshot.refresh_from_db()
            snapshot_data = AiDiagnosticSnapshotSerializer(snapshot).data

        return Response(
            {
                "user_message": AiMessageSerializer(user_message).data,
                "assistant_message": AiMessageSerializer(assistant_message).data,
                "diagnostic_snapshot": snapshot_data,
            },
            status=status.HTTP_202_ACCEPTED,
        )
