from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.organizations.serializers import OrganizationInvitationSerializer, OrganizationMembershipSerializer
from apps.organizations.services import (
    accept_organization_invitation_for_user,
    resolve_organization_invitation_token,
    validate_organization_invitation_for_email,
    validate_organization_invitation_for_user,
)

from .tokens import (
    validate_email_verification_token,
    validate_password_reset_token,
)

User = get_user_model()


def raise_serializer_validation_error(exc: DjangoValidationError) -> None:
    if hasattr(exc, "message_dict"):
        raise serializers.ValidationError(exc.message_dict) from exc
    raise serializers.ValidationError(exc.messages) from exc


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "email_verified",
            "is_active",
            "created_at",
            "updated_at",
            "last_login_at",
        )
        read_only_fields = fields


class AcceptedOrganizationInvitationResponseSerializer(serializers.Serializer):
    invitation = OrganizationInvitationSerializer()
    membership = OrganizationMembershipSerializer()


class UserResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    organization_invitation = AcceptedOrganizationInvitationResponseSerializer(required=False)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField(required=False)
    token_type = serializers.CharField()
    access_expires_in = serializers.IntegerField()
    refresh_expires_in = serializers.IntegerField(required=False)


class TokenLoginResponseSerializer(UserResponseSerializer):
    tokens = TokenPairSerializer()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField(required=False)
    token_type = serializers.CharField()
    access_expires_in = serializers.IntegerField()
    refresh_expires_in = serializers.IntegerField(required=False)


class TokenLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class RegisterResponseSerializer(DetailResponseSerializer):
    user = UserSerializer()
    organization_invitation = AcceptedOrganizationInvitationResponseSerializer(required=False)


class VerifyEmailResponseSerializer(DetailResponseSerializer):
    user = UserSerializer()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    organization_invitation_token = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name", "organization_invitation_token")

    def validate_email(self, value):
        normalized_value = User.objects.normalize_email(value)
        if User.objects.filter(email=normalized_value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        token = attrs.get("organization_invitation_token")
        if token:
            try:
                invitation = resolve_organization_invitation_token(token)
                validate_organization_invitation_for_email(invitation, attrs["email"])
            except DjangoValidationError as exc:
                raise_serializer_validation_error(exc)
            attrs["organization_invitation"] = invitation
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        token = validated_data.pop("organization_invitation_token", "")
        invitation = validated_data.pop("organization_invitation", None)
        user = User.objects.create_user(**validated_data, email_verified=False)
        from apps.organizations.services import get_or_create_personal_organization

        get_or_create_personal_organization(user)
        self.accepted_organization_invitation = None
        if token and invitation is not None:
            try:
                self.accepted_organization_invitation = accept_organization_invitation_for_user(invitation, user)
            except DjangoValidationError as exc:
                raise_serializer_validation_error(exc)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    organization_invitation_token = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is inactive."})
        if not user.email_verified:
            raise serializers.ValidationError({"detail": "Email address is not verified."})
        token = attrs.get("organization_invitation_token")
        if token:
            try:
                invitation = resolve_organization_invitation_token(token)
                validate_organization_invitation_for_user(invitation, user)
            except DjangoValidationError as exc:
                raise_serializer_validation_error(exc)
            attrs["organization_invitation"] = invitation
        attrs["user"] = user
        return attrs

    def accept_organization_invitation(self):
        invitation = self.validated_data.get("organization_invitation")
        if invitation is None:
            return None
        try:
            return accept_organization_invitation_for_user(invitation, self.validated_data["user"])
        except DjangoValidationError as exc:
            raise_serializer_validation_error(exc)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def get_user(self):
        email = User.objects.normalize_email(self.validated_data["email"])
        return User.objects.filter(email=email, is_active=True).first()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            email = validate_password_reset_token(attrs["token"])
        except signing.BadSignature as exc:
            raise serializers.ValidationError({"token": "Invalid or expired token."}) from exc
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({"token": "Invalid or expired token."}) from exc
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            email = validate_email_verification_token(attrs["token"])
        except signing.BadSignature as exc:
            raise serializers.ValidationError({"token": "Invalid or expired token."}) from exc
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({"token": "Invalid or expired token."}) from exc
        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified", "updated_at"])
        return user


def serialize_accepted_organization_invitation(accepted_organization_invitation):
    if accepted_organization_invitation is None:
        return None
    invitation, membership = accepted_organization_invitation
    return {
        "invitation": OrganizationInvitationSerializer(invitation).data,
        "membership": OrganizationMembershipSerializer(membership).data,
    }


def build_register_response(user, accepted_organization_invitation=None):
    response = {
        "user": UserSerializer(user).data,
        "detail": "User created successfully. Verification email sent.",
    }
    organization_invitation = serialize_accepted_organization_invitation(accepted_organization_invitation)
    if organization_invitation is not None:
        response["organization_invitation"] = organization_invitation
    return response


def build_login_response(user, accepted_organization_invitation=None):
    response = {"user": UserSerializer(user).data}
    organization_invitation = serialize_accepted_organization_invitation(accepted_organization_invitation)
    if organization_invitation is not None:
        response["organization_invitation"] = organization_invitation
    return response


def build_forgot_password_response(user):
    return {"detail": "If the account exists, password reset instructions have been sent."}
