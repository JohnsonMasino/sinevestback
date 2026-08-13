from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .exceptions import InsufficientFundsError
from .models import Wallet, WalletLedgerEntry
from .services import credit_available, debit_available


class BalanceCorrectionForm(forms.Form):
    DIRECTION_CHOICES = (
        ("credit", "Credit (add funds)"),
        ("debit", "Debit (remove funds)"),
    )

    direction = forms.ChoiceField(choices=DIRECTION_CHOICES)
    amount = forms.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    reason = forms.CharField(
        max_length=255,
        help_text="Required — recorded verbatim on the resulting ledger entry.",
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """
    Balance fields are read-only here on purpose: staff must never
    hand-edit them, since that would let the wallet drift from the
    transaction/trade history. The only sanctioned manual override is the
    "Correct balance" action below, which still routes through
    wallet/services.py and therefore still writes a WalletLedgerEntry.
    """

    list_display = ("user", "available_balance", "locked_balance", "total_balance_display", "correct_balance_link")
    search_fields = ("user__email",)
    readonly_fields = (
        "id",
        "user",
        "available_balance",
        "locked_balance",
        "total_deposited",
        "total_withdrawn",
        "total_profit_earned",
        "updated_at",
    )

    def total_balance_display(self, obj):
        return obj.total_balance

    total_balance_display.short_description = "Total Balance"

    def correct_balance_link(self, obj):
        url = reverse("admin:wallet_correct_balance", args=[obj.pk])
        return format_html('<a href="{}">Correct balance</a>', url)

    correct_balance_link.short_description = "Actions"

    def has_add_permission(self, request):
        # Wallets are only ever created via the post_save signal on User.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        custom_urls = [
            path(
                "<uuid:wallet_id>/correct-balance/",
                self.admin_site.admin_view(self.correct_balance_view),
                name="wallet_correct_balance",
            ),
        ]
        return custom_urls + super().get_urls()

    def correct_balance_view(self, request, wallet_id):
        wallet = Wallet.objects.filter(pk=wallet_id).first()
        if wallet is None:
            self.message_user(request, "Wallet not found.", level=messages.ERROR)
            return redirect("admin:wallet_wallet_changelist")

        if request.method == "POST":
            form = BalanceCorrectionForm(request.POST)
            if form.is_valid():
                amount = form.cleaned_data["amount"]
                reason = f"Admin correction: {form.cleaned_data['reason']}"
                try:
                    if form.cleaned_data["direction"] == "credit":
                        credit_available(wallet, amount, reason=reason)
                    else:
                        debit_available(wallet, amount, reason=reason)
                except InsufficientFundsError as exc:
                    form.add_error(None, str(exc))
                else:
                    self.message_user(
                        request, "Balance corrected and ledger entry recorded.", level=messages.SUCCESS
                    )
                    return redirect(reverse("admin:wallet_wallet_change", args=[wallet.pk]))
        else:
            form = BalanceCorrectionForm()

        context = {
            **self.admin_site.each_context(request),
            "title": f"Correct balance — {wallet.user.email}",
            "wallet": wallet,
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "wallet/admin_correct_balance.html", context)


@admin.register(WalletLedgerEntry)
class WalletLedgerEntryAdmin(admin.ModelAdmin):
    """Fully read-only — a system-generated audit trail, never hand-edited."""

    list_display = (
        "wallet",
        "entry_type",
        "amount",
        "balance_after_available",
        "balance_after_locked",
        "reference",
        "created_at",
    )
    list_filter = ("entry_type",)
    search_fields = ("wallet__user__email", "reference")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False