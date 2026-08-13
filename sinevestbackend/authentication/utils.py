import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from .models import OTP, PasswordResetToken


def generate_otp_code() -> str:
    """Returns a zero-padded 6-digit numeric OTP code."""
    return f"{secrets.randbelow(1000000):06d}"


def create_otp(user, purpose: str = "register") -> OTP:
    """
    Invalidates any prior unused OTP for this user/purpose and issues a fresh one.
    """
    OTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

    expiry_minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
    return OTP.objects.create(
        user=user,
        code=generate_otp_code(),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )


def create_password_reset_token(user):
    """
    Invalidates any prior unused reset tokens for this user, then issues a new
    one. Returns (PasswordResetToken instance, raw_token) — the raw token is
    only available here; only its hash is persisted.
    """
    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

    raw_token = secrets.token_urlsafe(32)
    expiry_minutes = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY_MINUTES", 30)
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=make_password(raw_token),
        expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
    )
    return reset_token, raw_token