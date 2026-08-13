import random

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from .models import PinChangeOTP, TransactionPin


def generate_numeric_otp(length: int = 6) -> str:
    """Generate a zero-padded numeric OTP string of the given length."""
    return str(random.randint(0, 10 ** length - 1)).zfill(length)


def otp_expiry():
    minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
    return timezone.now() + timezone.timedelta(minutes=minutes)


def verify_pin(user, raw_pin: str) -> bool:
    """
    Internal helper for other apps (e.g. withdrawal) to verify a user's
    transaction PIN. Not exposed as a public endpoint.

    Returns False if no PIN has been set yet, or if the pin doesn't match.
    """
    try:
        tp = user.transaction_pin
    except TransactionPin.DoesNotExist:
        return False

    if not tp.is_set:
        return False

    return check_password(raw_pin, tp.pin_hash)


def create_pin_change_otp(user, new_pin: str) -> PinChangeOTP:
    """
    Invalidates any prior unused PIN-change OTPs for this user, then
    creates a fresh one holding the hashed new PIN.
    """
    PinChangeOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    return PinChangeOTP.objects.create(
        user=user,
        code=generate_numeric_otp(),
        new_pin_hash=make_password(new_pin),
        expires_at=otp_expiry(),
    )


def get_latest_valid_pin_change_otp(user, code: str):
    otp = (
        PinChangeOTP.objects.filter(user=user, code=code, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if otp and otp.is_valid():
        return otp
    return None