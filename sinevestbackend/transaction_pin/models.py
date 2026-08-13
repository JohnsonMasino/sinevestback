import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


def default_pin_expiry():
    """
    Fallback used only if OTP_EXPIRY_MINUTES cannot be read from settings
    at import time. Actual expiry is always set explicitly when the row
    is created (see services.py).
    """
    return timezone.now()


class TransactionPin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transaction_pin",
    )
    pin_hash = models.CharField(
        max_length=128,
        help_text="Hashed 4-digit transaction PIN (Django make_password). Never stored or returned in plain text.",
    )
    is_set = models.BooleanField(
        default=False,
        help_text="Whether the user has completed their first-time PIN setup.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transaction_pin_transactionpin"
        verbose_name = "Transaction PIN"
        verbose_name_plural = "Transaction PINs"

    def __str__(self):
        return f"TransactionPin(user={self.user_id}, is_set={self.is_set})"


class PinChangeOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pin_change_otps",
    )
    code = models.CharField(max_length=6, help_text="6-digit numeric OTP, zero-padded.")
    new_pin_hash = models.CharField(
        max_length=128,
        help_text="Hashed pending new PIN, held here until the OTP is confirmed.",
    )
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(help_text="now() + OTP_EXPIRY_MINUTES at creation time.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transaction_pin_pinchangeotp"
        verbose_name = "PIN Change OTP"
        verbose_name_plural = "PIN Change OTPs"

    def __str__(self):
        return f"PinChangeOTP(user={self.user_id}, used={self.is_used})"

    def is_valid(self):
        return (not self.is_used) and self.expires_at > timezone.now()