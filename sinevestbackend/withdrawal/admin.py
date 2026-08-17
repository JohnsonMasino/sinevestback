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
        # `status` is locked on every EXISTING withdrawal, in every state.
        # The only sanctioned way to move a saved withdrawal to
        # completed/rejected is through the mark_completed / mark_rejected
        # actions (and, for brand-new records, save_model below) — these
        # are the only code paths that call wallet.services.debit_available().
        # `created_at` and `processed_at` are deliberately left OUT of this
        # list so an admin can correct/backdate/postdate them freely —
        # that change is display-only and has no wallet effect.
        if obj is None:
            # Add page: an admin creating a withdrawal manually needs to
            # set user/amount/wallet_address/network, and may optionally
            # pick a final status (see save_model) — nothing is locked yet.
            return ["id"]
        always_readonly = ["id", "user", "amount", "wallet_address", "network", "status"]
        if obj.status in (Withdrawal.Status.COMPLETED, Withdrawal.Status.REJECTED):
            # Notes are locked once resolved so the record of "why" can't be rewritten after the fact.
            return always_readonly + ["admin_notes"]
        return always_readonly

    def get_changeform_initial_data(self, request):
        # Manually-created withdrawals skip the OTP step, so default the add
        # form to "pending" rather than the model's own default of
        # "pending_otp" (which only makes sense for the user-facing flow).
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("status", Withdrawal.Status.PENDING)
        return initial

    # ------------------------------------------------------------------
    # Shared complete/reject logic, used by both the bulk actions and
    # manual creation from the admin (save_model below).
    # ------------------------------------------------------------------

    def _complete(self, request, withdrawal):
        if withdrawal.status != Withdrawal.Status.PENDING:
            self.message_user(
                request,
                f"Skipped {withdrawal.id}: only 'pending' withdrawals can be completed.",
                level=messages.WARNING,
            )
            return False

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
            return False

        send_withdrawal_completed_email(withdrawal.user, withdrawal)
        return True

    def _reject(self, request, withdrawal):
        if withdrawal.status != Withdrawal.Status.PENDING:
            self.message_user(
                request,
                f"Skipped {withdrawal.id}: only 'pending' withdrawals can be rejected.",
                level=messages.WARNING,
            )
            return False

        withdrawal.status = Withdrawal.Status.REJECTED
        withdrawal.processed_at = timezone.now()
        withdrawal.save(update_fields=["status", "processed_at"])
        send_withdrawal_rejected_email(withdrawal.user, withdrawal)
        return True

    # ------------------------------------------------------------------
    # Bulk actions (select rows in the list view)
    # ------------------------------------------------------------------

    @admin.action(description="Mark selected PENDING withdrawals as COMPLETED (debits wallet)")
    def mark_completed(self, request, queryset):
        completed_count = sum(1 for withdrawal in queryset for _ in [self._complete(request, withdrawal)] if _)
        if completed_count:
            self.message_user(request, f"{completed_count} withdrawal(s) marked completed.", level=messages.SUCCESS)

    @admin.action(description="Mark selected PENDING withdrawals as REJECTED")
    def mark_rejected(self, request, queryset):
        rejected_count = sum(1 for withdrawal in queryset for _ in [self._reject(request, withdrawal)] if _)
        if rejected_count:
            self.message_user(request, f"{rejected_count} withdrawal(s) marked rejected.", level=messages.SUCCESS)

    # ------------------------------------------------------------------
    # Manual creation from the admin: a brand-new withdrawal is always
    # persisted first as "pending" (no wallet effect, skips pending_otp
    # entirely since there's no OTP step for an admin-entered request),
    # then routed through the same _complete/_reject logic as the bulk
    # actions if the admin chose a final status on the same add form.
    # Existing withdrawals are untouched here — status stays locked via
    # get_readonly_fields, so this is just a normal save for them.
    # ------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not change:
            desired_status = obj.status
            obj.status = Withdrawal.Status.PENDING
            obj.processed_at = None
            super().save_model(request, obj, form, change)

            if desired_status == Withdrawal.Status.COMPLETED:
                self._complete(request, obj)
            elif desired_status == Withdrawal.Status.REJECTED:
                self._reject(request, obj)
            # else: left as "pending" (covers a chosen status of
            # pending_otp or pending too — both just mean "leave it pending").
            return

        super().save_model(request, obj, form, change)


@admin.register(WithdrawalOTP)
class WithdrawalOTPAdmin(admin.ModelAdmin):
    """Read-only for direct add/change — for debugging only. Delete is
    explicitly allowed so an admin can delete a Withdrawal and let this
    cascade-delete along with it; without this override, Django's cascade
    permission check blocks the whole "Delete multiple objects" action
    whenever a related WithdrawalOTP row exists."""

    list_display = ("withdrawal", "code", "is_used", "expires_at", "created_at")
    search_fields = ("withdrawal__id", "withdrawal__user__email")
    list_filter = ("is_used",)
    readonly_fields = [f.name for f in WithdrawalOTP._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True