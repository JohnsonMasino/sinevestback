from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from wallet.services import InsufficientFundsError, debit_available

from .emails import send_withdrawal_completed_email, send_withdrawal_rejected_email
from .models import Withdrawal, WithdrawalOTP


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "wallet_address", "status", "created_at", "processed_at")
    list_filter = ("status", "network")
    search_fields = ("user__email", "wallet_address")
    actions = ["mark_completed", "mark_rejected"]

    def get_queryset(self, request):
        # pending_otp rows are not yet confirmed by the user and are not
        # actionable — still visible for visibility, but clearly excluded
        # from the default actionable set via list_filter above.
        return super().get_queryset(request)

    def get_readonly_fields(self, request, obj=None):
        always_readonly = ["id", "user", "amount", "wallet_address", "network", "created_at", "processed_at"]
        if obj and obj.status in (Withdrawal.Status.COMPLETED, Withdrawal.Status.REJECTED):
            # Fully locked once resolved.
            return always_readonly + ["status", "admin_notes"]
        return always_readonly

    @admin.action(description="Mark selected PENDING withdrawals as COMPLETED (debits wallet)")
    def mark_completed(self, request, queryset):
        completed_count = 0
        for withdrawal in queryset:
            if withdrawal.status != Withdrawal.Status.PENDING:
                self.message_user(
                    request,
                    f"Skipped {withdrawal.id}: only 'pending' withdrawals can be completed.",
                    level=messages.WARNING,
                )
                continue

            try:
                with transaction.atomic():
                    debit_available(
                        withdrawal.user.wallet,
                        withdrawal.amount,
                        reason=f"Withdrawal #{withdrawal.id}",
                    )
                    withdrawal.status = Withdrawal.Status.COMPLETED
                    withdrawal.processed_at = timezone.now()
                    withdrawal.save(update_fields=["status", "processed_at"])
            except InsufficientFundsError:
                self.message_user(
                    request,
                    f"Skipped {withdrawal.id}: user no longer has sufficient available balance.",
                    level=messages.ERROR,
                )
                continue

            send_withdrawal_completed_email(withdrawal.user, withdrawal)
            completed_count += 1

        if completed_count:
            self.message_user(request, f"{completed_count} withdrawal(s) marked completed.", level=messages.SUCCESS)

    @admin.action(description="Mark selected PENDING withdrawals as REJECTED")
    def mark_rejected(self, request, queryset):
        rejected_count = 0
        for withdrawal in queryset:
            if withdrawal.status != Withdrawal.Status.PENDING:
                self.message_user(
                    request,
                    f"Skipped {withdrawal.id}: only 'pending' withdrawals can be rejected.",
                    level=messages.WARNING,
                )
                continue

            withdrawal.status = Withdrawal.Status.REJECTED
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=["status", "processed_at"])
            send_withdrawal_rejected_email(withdrawal.user, withdrawal)
            rejected_count += 1

        if rejected_count:
            self.message_user(request, f"{rejected_count} withdrawal(s) marked rejected.", level=messages.SUCCESS)


@admin.register(WithdrawalOTP)
class WithdrawalOTPAdmin(admin.ModelAdmin):
    """Read-only, for debugging only."""

    list_display = ("withdrawal", "code", "is_used", "expires_at", "created_at")
    search_fields = ("withdrawal__id", "withdrawal__user__email")
    list_filter = ("is_used",)
    readonly_fields = [f.name for f in WithdrawalOTP._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False