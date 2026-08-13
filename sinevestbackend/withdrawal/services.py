import random

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Withdrawal, WithdrawalOTP


def generate_numeric_otp(length: int = 6) -> str:
    return str(random.randint(0, 10 ** length - 1)).zfill(length)


def otp_expiry():
    minutes = getattr(settings, "OTP_EXPIRY_MINUTES", 10)
    return timezone.now() + timezone.timedelta(minutes=minutes)


def create_withdrawal_otp(withdrawal: Withdrawal) -> WithdrawalOTP:
    return WithdrawalOTP.objects.create(
        withdrawal=withdrawal,
        code=generate_numeric_otp(),
        expires_at=otp_expiry(),
    )


def get_valid_otp(withdrawal: Withdrawal, code: str):
    try:
        otp = withdrawal.otp
    except WithdrawalOTP.DoesNotExist:
        return None

    if otp.is_used or otp.code != code or otp.expires_at <= timezone.now():
        return None
    return otp


def pending_amount_total(user) -> "Decimal":
    """
    Sum of amounts across the user's own pending_otp + pending withdrawals.
    Used so a user can't stack multiple in-flight requests beyond what they
    actually have available.
    """
    from django.db.models import Sum
    from decimal import Decimal

    total = Withdrawal.objects.filter(
        user=user,
        status__in=[Withdrawal.Status.PENDING_OTP, Withdrawal.Status.PENDING],
    ).aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0.00")


def cleanup_abandoned_withdrawals() -> int:
    """
    Deletes Withdrawal rows (and their OTPs, via CASCADE) still in
    status="pending_otp" older than PENDING_TRANSACTION_EXPIRY_MINUTES.

    No wallet funds were ever locked at this stage, so deletion is safe
    and requires no balance reversal.

    Intended to be called from the shared cron endpoint
    (POST /api/cron/cleanup-pending-transactions/), which lives alongside
    the trade app's cron views per the project's cron design, and which
    also calls the deposit app's equivalent cleanup for forward-compatibility.
    """
    minutes = getattr(settings, "PENDING_TRANSACTION_EXPIRY_MINUTES", 5)
    cutoff = timezone.now() - timezone.timedelta(minutes=minutes)

    with transaction.atomic():
        qs = Withdrawal.objects.select_for_update().filter(
            status=Withdrawal.Status.PENDING_OTP,
            created_at__lt=cutoff,
        )
        count = qs.count()
        qs.delete()

    return count