from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from wallet.models import Wallet
from wallet.services import credit_available

from .emails import send_deposit_approved_email, send_deposit_rejected_email
from .models import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "status", "created_at", "processed_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__email")
    ordering = ("-created_at",)

    # id, user, and amount stay immutable. created_at and processed_at are
    # intentionally left editable so an admin can correct/backdate/postdate
    # them for display purposes in transaction history.
    readonly_fields = ("id", "user", "amount")

    fields = ("id", "user", "amount", "status", "admin_notes", "created_at", "processed_at")

    actions = ["approve_deposits", "reject_deposits"]

    # ------------------------------------------------------------------
    # Shared approve/reject logic, used by both bulk actions and the
    # individual detail-page save.
    # ------------------------------------------------------------------

    def _approve(self, request, deposit):
        if deposit.status != "pending":
            self.message_user(
                request,
                f"Deposit {deposit.id} is already '{deposit.status}' — skipped to avoid double-crediting.",
                level=messages.WARNING,
            )
            return False

        try:
            wallet = Wallet.objects.get(user=deposit.user)
        except Wallet.DoesNotExist:
            self.message_user(
                request,
                f"Deposit {deposit.id}: user {deposit.user.email} has no wallet — skipped.",
                level=messages.ERROR,
            )
            return False

        with transaction.atomic():
            credit_available(wallet, deposit.amount, reason=f"Deposit {deposit.id} approved by {request.user.email}")
            deposit.status = "approved"
            deposit.processed_at = timezone.now()
            deposit.save(update_fields=["status", "processed_at"])

        send_deposit_approved_email(deposit.user, deposit)
        return True

    def _reject(self, request, deposit):
        if deposit.status != "pending":
            self.message_user(
                request,
                f"Deposit {deposit.id} is already '{deposit.status}' — skipped.",
                level=messages.WARNING,
            )
            return False

        deposit.status = "rejected"
        deposit.processed_at = timezone.now()
        deposit.save(update_fields=["status", "processed_at"])

        send_deposit_rejected_email(deposit.user, deposit)
        return True

    # ------------------------------------------------------------------
    # Bulk actions (select rows in the list view)
    # ------------------------------------------------------------------

    @admin.action(description="Approve selected deposits (credits wallet)")
    def approve_deposits(self, request, queryset):
        approved = sum(1 for deposit in queryset for _ in [self._approve(request, deposit)] if _)
        if approved:
            self.message_user(request, f"{approved} deposit(s) approved and credited.", level=messages.SUCCESS)

    @admin.action(description="Reject selected deposits")
    def reject_deposits(self, request, queryset):
        rejected = sum(1 for deposit in queryset for _ in [self._reject(request, deposit)] if _)
        if rejected:
            self.message_user(request, f"{rejected} deposit(s) rejected.", level=messages.SUCCESS)

    # ------------------------------------------------------------------
    # Individual detail-page save: if the admin changes `status` on the
    # change form and saves, route it through the same approve/reject
    # logic instead of just overwriting the field directly. Any other
    # changed fields (created_at, admin_notes) are persisted independently
    # so they're never silently dropped by _approve/_reject's own
    # update_fields=["status", "processed_at"] save.
    # ------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not change or "status" not in form.changed_data:
            # New object (shouldn't normally happen — deposits are created
            # via the API) or no status change: save as-is.
            super().save_model(request, obj, form, change)
            return

        previous_status = Deposit.objects.get(pk=obj.pk).status
        new_status = obj.status

        # Reset to the DB value first so _approve/_reject's own status
        # check and save() call are the single source of truth for the
        # status transition itself.
        obj.status = previous_status

        # Persist any other changed fields (e.g. a corrected created_at)
        # up front, independent of the status branch below.
        other_changed_fields = [f for f in form.changed_data if f != "status"]
        if other_changed_fields:
            obj.save(update_fields=other_changed_fields)

        if new_status == "approved":
            self._approve(request, obj)
        elif new_status == "rejected":
            self._reject(request, obj)
        else:
            # e.g. admin manually set it back to "pending".
            obj.status = new_status
            super().save_model(request, obj, form, change)