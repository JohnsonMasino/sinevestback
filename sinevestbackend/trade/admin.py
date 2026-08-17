from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.contrib import admin
from django.db import transaction
from django.utils import timezone

from wallet.services import lock_funds

from .emails import send_trade_activated_email
from .models import Trade, TradePlan


@admin.register(TradePlan)
class TradePlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "min_amount", "max_amount", "profit_percentage", "duration_hours", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")

    def get_readonly_fields(self, request, obj=None):
        # code is the seeded primary key — read-only after creation, but
        # editable (in theory) when adding a brand-new plan row manually.
        if obj:
            return ("code",)
        return ()

    def has_add_permission(self, request):
        # Plans are seeded via data migration; discourage ad-hoc creation
        # from the admin, but don't hard-block it in case a 6th plan is
        # ever needed for a demo.
        return True

    def has_delete_permission(self, request, obj=None):
        return False


class TradeAdminAddForm(forms.ModelForm):
    """
    Used only on the "Add trade" page. Mirrors the exact validation
    TradeCreateSerializer.validate() applies for a user-initiated trade —
    plan must be active, amount must fall within the plan's min/max, and
    amount can't exceed the chosen user's available wallet balance — so a
    manually-opened trade can never bypass those business rules and leave
    the wallet in a state the frontend flow could never produce.
    """

    class Meta:
        model = Trade
        fields = ["user", "plan", "amount", "started_at"]

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        plan = cleaned_data.get("plan")
        amount = cleaned_data.get("amount")

        if not (user and plan and amount is not None):
            # Required-field errors already surfaced individually; nothing
            # further to cross-check.
            return cleaned_data

        if not plan.is_active:
            self.add_error("plan", "This plan is not currently active.")
            return cleaned_data

        if amount < plan.min_amount or (plan.max_amount is not None and amount > plan.max_amount):
            if plan.max_amount is not None:
                message = f"Amount must be between ${plan.min_amount} and ${plan.max_amount} for the {plan.name}."
            else:
                message = f"Amount must be at least ${plan.min_amount} for the {plan.name}."
            self.add_error("amount", message)

        wallet = getattr(user, "wallet", None)
        if wallet is None:
            self.add_error("user", "This user has no wallet.")
        elif amount > wallet.available_balance:
            self.add_error("amount", "Amount exceeds this user's available wallet balance.")

        return cleaned_data


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan", "amount", "status", "started_at", "matures_at", "closed_at")
    list_filter = ("status", "plan")
    search_fields = ("user__email",)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = TradeAdminAddForm
        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if obj is None:
            # Add page: only the inputs a real trade actually needs from a
            # human. profit_percentage, duration_hours, expected_profit,
            # matures_at, and status are all derived from the chosen plan
            # in save_model below, the same way TradeCreateSerializer does.
            return ("user", "plan", "amount", "started_at")
        return super().get_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        # Everything stays locked EXCEPT the three timestamps. Trade closure
        # (status + actual_profit_paid) must only ever happen through the
        # cron endpoint, since that's the single code path that calls
        # wallet.services.unlock_and_credit() — letting status be edited
        # here would reproduce the exact bug we just fixed on withdrawals.
        if obj is None:
            # Add page: user/plan/amount/started_at are freely editable
            # (validated by TradeAdminAddForm above); nothing to lock yet.
            return ()
        editable_fields = ("started_at", "matures_at", "closed_at")
        return [f.name for f in Trade._meta.fields if f.name not in editable_fields]

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    # ------------------------------------------------------------------
    # Manual creation from the admin: snapshots the chosen plan's terms
    # exactly the way TradeCreateSerializer.create() does, locks the
    # principal from the user's wallet, and saves — all in one transaction.
    # By the time this runs, TradeAdminAddForm.clean() has already verified
    # the plan is active, the amount is in range, and the user can afford
    # it, so this only has to do the arithmetic and the lock.
    # ------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not change:
            plan = obj.plan
            started_at = obj.started_at or timezone.now()

            obj.profit_percentage = plan.profit_percentage
            obj.duration_hours = plan.duration_hours
            obj.expected_profit = (obj.amount * plan.profit_percentage / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            obj.started_at = started_at
            obj.matures_at = started_at + timezone.timedelta(hours=plan.duration_hours)
            obj.status = Trade.Status.ACTIVE

            with transaction.atomic():
                lock_funds(
                    obj.user.wallet,
                    obj.amount,
                    reason=f"Trade lock - {plan.name} (added by {request.user.email})",
                )
                super().save_model(request, obj, form, change)

            send_trade_activated_email(obj.user, obj)
            return

        super().save_model(request, obj, form, change)