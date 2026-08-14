from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
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
    ErrorDetailSerializer,
    ForgotPasswordSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MessageResponseSerializer,
    RegisterResponseSerializer,
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
    """
    POST /api/auth/register/

    Creates a new account and emails a 6-digit OTP for verification. The
    account is created immediately in an unverified state (is_verified=False)
    and cannot log in until the OTP is confirmed via
    POST /api/auth/verify-otp/. No token is issued by this endpoint.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a new account",
        description=(
            "Creates a new, unverified account and emails a 6-digit OTP to the given address. "
            "The response does NOT include an access/refresh token — the frontend should route "
            "the user to an 'enter OTP' screen next, then call /api/auth/verify-otp/, then "
            "/api/auth/login/."
        ),
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=RegisterResponseSerializer,
                description="Account created; OTP emailed.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "message": "Registration successful. Check your email for the OTP.",
                            "email": "jane@example.com",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Validation error — field name(s) map to a list of error messages.",
                examples=[
                    OpenApiExample(
                        "Email already taken",
                        value={"email": ["An account with this email already exists."]},
                    ),
                    OpenApiExample(
                        "Passwords don't match",
                        value={"confirm_password": ["Passwords do not match."]},
                    ),
                    OpenApiExample(
                        "Weak password",
                        value={"password": ["This password is too common."]},
                    ),
                    OpenApiExample(
                        "Missing name field",
                        value={"first_name": ["This field is required."]},
                    ),
                ],
            ),
        },
    )
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
    """
    POST /api/auth/verify-otp/

    Confirms the OTP sent at registration and flips the account to
    is_verified=True. Does NOT log the user in — no token is returned;
    the frontend should redirect to the login screen afterward.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Confirm registration OTP",
        description="Marks the account as verified. Does not log the user in — no token is returned here.",
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(
                response=MessageResponseSerializer,
                description="Email verified successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Email verified successfully. You can now log in."},
                    )
                ],
            ),
            400: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="OTP is invalid, already used, or expired.",
                examples=[OpenApiExample("Invalid OTP", value={"detail": "Invalid or expired OTP."})],
            ),
            404: OpenApiResponse(
                response=ErrorDetailSerializer, description="No account exists for the given email."
            ),
        },
    )
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
    """
    POST /api/auth/resend-otp/

    Issues a fresh registration OTP. Rate-limited to one request per 60
    seconds per user to prevent email spamming.
    """

    permission_classes = [AllowAny]
    RESEND_COOLDOWN_SECONDS = 60

    @extend_schema(
        summary="Resend registration OTP",
        description="Sends a new 6-digit OTP to the given email. Rate-limited to one request per 60 seconds.",
        request=ResendOTPSerializer,
        responses={
            200: OpenApiResponse(
                response=MessageResponseSerializer,
                examples=[OpenApiExample("Success", value={"message": "A new OTP has been sent to your email."})],
            ),
            404: OpenApiResponse(
                response=ErrorDetailSerializer, description="No account exists for the given email."
            ),
            429: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Too soon since the last OTP was sent.",
                examples=[
                    OpenApiExample(
                        "Rate limited",
                        value={"detail": "Please wait a minute before requesting another OTP."},
                    )
                ],
            ),
        },
    )
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
    POST /api/auth/login/

    Deliberately does NOT use Django's authenticate()/ModelBackend, since
    that silently blocks is_active=False users. Login must succeed for
    inactive accounts (only account-active status blocks state-changing
    actions elsewhere in the platform); only is_verified gates login here.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Log in",
        description=(
            "Exchanges email + password for a JWT access/refresh pair. Login succeeds even if "
            "the account has been deactivated by an admin (is_active=False) — deactivation only "
            "blocks state-changing actions elsewhere, not login itself. Login FAILS if the "
            "account's email has not yet been verified via OTP."
        ),
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=LoginResponseSerializer,
                description="Login successful.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIs...",
                            "refresh": "eyJhbGciOiJIUzI1NiIs...",
                            "user": {
                                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                "email": "jane@example.com",
                                "first_name": "Jane",
                                "last_name": "Doe",
                                "is_verified": True,
                                "is_active": True,
                                "date_joined": "2026-08-01T10:00:00Z",
                            },
                        },
                    )
                ],
            ),
            401: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Email/password combination is incorrect.",
                examples=[OpenApiExample("Bad credentials", value={"detail": "Invalid email or password."})],
            ),
            403: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Account exists but email is not yet verified.",
                examples=[
                    OpenApiExample(
                        "Unverified", value={"detail": "Please verify your email before logging in."}
                    )
                ],
            ),
        },
    )
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
    POST /api/auth/forgot-password/

    Always returns the same generic 200 message whether or not the email
    exists, to avoid leaking which emails are registered (user enumeration
    protection). If the account exists, a reset link is emailed.
    """

    permission_classes = [AllowAny]
    GENERIC_MESSAGE = "If an account exists for this email, a reset link has been sent."

    @extend_schema(
        summary="Request a password reset link",
        description=(
            "Always returns 200 with the same generic message, regardless of whether the email "
            "exists, to prevent account enumeration. If it does exist, an email containing a "
            "reset link (with a token embedded in the URL) is sent."
        ),
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(
                response=MessageResponseSerializer,
                examples=[
                    OpenApiExample(
                        "Always this shape, regardless of whether the email exists",
                        value={"message": "If an account exists for this email, a reset link has been sent."},
                    )
                ],
            ),
        },
    )
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
    """
    POST /api/auth/reset-password-confirm/

    Sets a new password using the {id, token} pair embedded in the reset
    link's URL (e.g. {FRONTEND_URL}/reset-password/{id}/{token}). The
    frontend should parse both values out of the URL and submit them here
    alongside the new password.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Confirm password reset",
        description=(
            "Sets a new password using the {id, token} pair from the reset link's URL. Both "
            "values must be extracted from the link the user received by email — "
            "'{FRONTEND_URL}/reset-password/{id}/{token}'."
        ),
        request=ResetPasswordConfirmSerializer,
        responses={
            200: OpenApiResponse(
                response=MessageResponseSerializer,
                examples=[
                    OpenApiExample("Success", value={"message": "Password has been reset successfully."})
                ],
            ),
            400: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Token is invalid, already used, expired, or passwords didn't match / failed validation.",
                examples=[
                    OpenApiExample("Bad link", value={"detail": "Invalid or expired reset link."}),
                    OpenApiExample(
                        "Passwords don't match", value={"confirm_password": ["Passwords do not match."]}
                    ),
                ],
            ),
        },
    )
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

    @extend_schema(
        summary="Get current user",
        description="Returns the authenticated user's own basic account info. Requires a valid access token.",
        responses={200: UserSerializer},
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)