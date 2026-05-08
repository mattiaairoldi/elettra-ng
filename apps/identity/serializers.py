from django.core import signing
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .tokens import (
    validate_email_verification_token,
    validate_password_reset_token,
)

User = get_user_model()


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


class UserResponseSerializer(serializers.Serializer):
    user = UserSerializer()


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class RegisterResponseSerializer(DetailResponseSerializer):
    user = UserSerializer()


class VerifyEmailResponseSerializer(DetailResponseSerializer):
    user = UserSerializer()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def validate_email(self, value):
        normalized_value = User.objects.normalize_email(value)
        if User.objects.filter(email=normalized_value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

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
        attrs["user"] = user
        return attrs


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


def build_register_response(user):
    return {
        "user": UserSerializer(user).data,
        "detail": "User created successfully. Verification email sent.",
    }


def build_forgot_password_response(user):
    return {"detail": "If the account exists, password reset instructions have been sent."}
