from django.contrib.auth import login, logout
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    DetailResponseSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    RegisterResponseSerializer,
    ResetPasswordSerializer,
    UserResponseSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    VerifyEmailResponseSerializer,
    build_forgot_password_response,
    build_login_response,
    build_register_response,
)
from .tasks import send_password_reset_email_task, send_verification_email_task


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: RegisterResponseSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_verification_email_task.delay(user.id)
        return Response(
            build_register_response(user, serializer.accepted_organization_invitation),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: UserResponseSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        accepted_organization_invitation = serializer.accept_organization_invitation()
        login(request, user)
        user.refresh_from_db(fields=["last_login", "last_login_at", "updated_at"])
        return Response(build_login_response(user, accepted_organization_invitation))


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: UserResponseSerializer})
    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=ForgotPasswordSerializer, responses={202: DetailResponseSerializer})
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        if user is not None:
            send_password_reset_email_task.delay(user.id)
        return Response(build_forgot_password_response(user), status=status.HTTP_202_ACCEPTED)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=ResetPasswordSerializer, responses={200: DetailResponseSerializer})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."})


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=VerifyEmailSerializer, responses={200: VerifyEmailResponseSerializer})
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"detail": "Email verified successfully.", "user": UserSerializer(user).data})
