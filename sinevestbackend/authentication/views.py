from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .emails import (
    send_password_changed_email,
    send_password_reset_email,
    send_registration_otp_email,
)
from .models import OTP, PasswordResetToken
from .serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    ResetPasswordConfirmSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from .utils import create_otp, create_password_reset_token

User = get_user_model()


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    """POST /api/auth/register/ — create account, send OTP."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            is_verified=False,
        )
        otp = create_otp(user, purpose="register")
        send_registration_otp_email(user, otp.code)

        return Response(
            {"message": "Registration successful. Check your email for the OTP.", "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    """POST /api/auth/verify-otp/ — confirm OTP, mark account verified."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_code = serializer.validated_data["otp_code"]

        user = get_object_or_404(User, email__iexact=email)
        otp = (
            OTP.objects.filter(user=user, code=otp_code, purpose="register", is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp or not otp.is_valid():
            return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user.is_verified = True
        user.save(update_fields=["is_verified"])

        return Response(
            {"message": "Email verified successfully. You can now log in."}, status=status.HTTP_200_OK
        )


class ResendOTPView(APIView):
    """POST /api/auth/resend-otp/ — re-send a fresh registration OTP."""

    permission_classes = [AllowAny]
    RESEND_COOLDOWN_SECONDS = 60

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = get_object_or_404(User, email__iexact=email)

        last_otp = OTP.objects.filter(user=user, purpose="register").order_by("-created_at").first()
        if last_otp and (timezone.now() - last_otp.created_at).total_seconds() < self.RESEND_COOLDOWN_SECONDS:
            return Response(
                {"detail": "Please wait a minute before requesting another OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp = create_otp(user, purpose="register")
        send_registration_otp_email(user, otp.code)

        return Response({"message": "A new OTP has been sent to your email."}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    POST /api/auth/login/ — email + password -> access/refresh token.
    Deliberately does NOT use Django's authenticate()/ModelBackend, since
    that silently blocks is_active=False users. Login must succeed for
    inactive accounts; only is_verified gates login.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email__iexact=email).first()
        if user is None or not user.check_password(password):
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response(
                {"detail": "Please verify your email before logging in."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = _tokens_for_user(user)
        return Response({**tokens, "user": UserSerializer(user).data}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/ — send password reset link.
    Always returns a generic message to avoid user enumeration.
    """

    permission_classes = [AllowAny]
    GENERIC_MESSAGE = "If an account exists for this email, a reset link has been sent."

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email).first()
        if user is not None:
            reset_token, raw_token = create_password_reset_token(user)
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{reset_token.id}/{raw_token}"
            send_password_reset_email(user, reset_link)

        return Response({"message": self.GENERIC_MESSAGE}, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    """POST /api/auth/reset-password-confirm/ — set new password via id + token."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reset_token = PasswordResetToken.objects.filter(id=data["id"], is_used=False).first()
        if (
            not reset_token
            or not reset_token.is_valid()
            or not check_password(data["token"], reset_token.token)
        ):
            return Response({"detail": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

        user = reset_token.user
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])

        reset_token.is_used = True
        reset_token.save(update_fields=["is_used"])

        # Invalidate any other outstanding reset tokens for this user.
        PasswordResetToken.objects.filter(user=user, is_used=False).exclude(pk=reset_token.pk).update(
            is_used=True
        )

        send_password_changed_email(user)

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class MeView(APIView):
    """GET /api/auth/me/ — return the current authenticated user's basic info."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)