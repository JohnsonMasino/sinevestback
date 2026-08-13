import uuid
from django.conf import settings
from django.db import models


class Withdrawal(models.Model):
    class Status(models.TextChoices):
        PENDING_OTP = "pending_otp", "Pending OTP"
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawals",
    )
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        help_text="Must be >= MIN_WITHDRAWAL_AMOUNT and <= available balance at request time.",
    )
    wallet_address = models.CharField(
        max_length=255,
        help_text="Destination USDT-TRC20 wallet address.",
    )
    network = models.CharField(
        max_length=50,
        default="USDT-TRC20",
        help_text="Fixed — the only supported payout network.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_OTP,
        help_text="pending_otp -> pending -> completed/rejected.",
    )
    admin_notes = models.TextField(blank=True)

    # Immutable — never exposed as editable in API or admin.
    created_at = models.DateTimeField(auto_now_add=True)
    # Auto-set server-side by admin.py when status moves to completed/rejected.
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "withdrawal_withdrawal"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Withdrawal({self.id}, user={self.user_id}, amount={self.amount}, status={self.status})"


class WithdrawalOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    withdrawal = models.OneToOneField(
        Withdrawal,
        on_delete=models.CASCADE,
        related_name="otp",
    )
    code = models.CharField(max_length=6, help_text="6-digit numeric OTP, zero-padded.")
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(help_text="now() + OTP_EXPIRY_MINUTES at creation time.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "withdrawal_withdrawalotp"

    def __str__(self):
        return f"WithdrawalOTP(withdrawal={self.withdrawal_id}, used={self.is_used})"