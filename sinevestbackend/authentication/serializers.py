from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


# ---------------------------------------------------------------------------
# Shared / reusable
# ---------------------------------------------------------------------------


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only representation of a User, reused wherever the API returns a
    full user object (e.g. inside the login response, and on GET /me/).
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_verified", "is_active", "date_joined"]
        read_only_fields = fields


class MessageResponseSerializer(serializers.Serializer):
    """Docs-only: generic {"message": "..."} response shape, reused across several endpoints."""

    message = serializers.CharField()


class ErrorDetailSerializer(serializers.Serializer):
    """Docs-only: generic {"detail": "..."} error response shape, reused across several endpoints."""

    detail = serializers.CharField()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="A unique, valid email address.")
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        help_text="Account password. Must satisfy Django's configured password validators.",
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, help_text="Must match password."
    )
    first_name = serializers.CharField(max_length=150, help_text="User's first name.")
    last_name = serializers.CharField(max_length=150, help_text="User's last name.")

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs


class RegisterResponseSerializer(serializers.Serializer):
    """Docs-only: shape of the 201 response from POST /api/auth/register/."""

    message = serializers.CharField()
    email = serializers.EmailField()


# ---------------------------------------------------------------------------
# OTP verification
# ---------------------------------------------------------------------------


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email address used at registration.")
    otp_code = serializers.CharField(max_length=6, min_length=6, help_text="6-digit OTP sent to the email.")


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Email address to resend the registration OTP to.")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Registered email address.")
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, help_text="Account password."
    )


class LoginResponseSerializer(serializers.Serializer):
    """Docs-only: shape of the 200 response from POST /api/auth/login/."""

    access = serializers.CharField(help_text="Short-lived JWT access token. Send as 'Authorization: Bearer <access>'.")
    refresh = serializers.CharField(help_text="Long-lived JWT refresh token. Used against /api/auth/token/refresh/.")
    user = UserSerializer()


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="Email address to send a password reset link to, if an account exists."
    )


class ResetPasswordConfirmSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="PasswordResetToken id, taken from the reset link.")
    token = serializers.CharField(help_text="Raw reset token, taken from the reset link.")
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, help_text="New account password."
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, help_text="Must match new_password."
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["new_password"])
        return attrs