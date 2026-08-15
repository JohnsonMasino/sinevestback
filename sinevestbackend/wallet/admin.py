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
    Full edit/delete access for manual corrections — e.g. fixing seed/test
    data, or reconciling a balance after something like the withdrawal bug
    that let a status change bypass debit_available().

    IMPORTANT: editing available_balance / locked_balance / etc. directly
    here does NOT write a WalletLedgerEntry. For any real balance movement
    prefer wallet.services (credit_available / debit_available / lock_funds
    / unlock_and_credit) so the ledger stays a true audit trail. Reserve
    direct admin edits for one-off corrections, and consider adding a
    matching WalletLedgerEntry by hand alongside any manual balance edit so
    the audit trail still explains the change.
    """

    list_display = (
        "id",
        "user",
        "available_balance",
        "locked_balance",
        "total_balance_display",
        "total_deposited",
        "total_withdrawn",
        "total_profit_earned",
        "updated_at",
    )
    search_fields = ("user__email",)
    ordering = ("-updated_at",)

    # `user` stays read-only: each user gets exactly one wallet via the
    # post_save signal, so reassigning it here could orphan or duplicate
    # wallets. `updated_at` is auto_now, so it can never be form-editable
    # regardless of this list — Django forces that at the model level.
    readonly_fields = ("id", "user", "updated_at")

    fields = (
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

    total_balance_display.short_description = "Total balance"


@admin.register(WalletLedgerEntry)
class WalletLedgerEntryAdmin(admin.ModelAdmin):
    """
    Full edit/delete access, same caveat as above: this table is the audit
    trail. Only edit/delete entries here for genuine corrections (e.g.
    removing a duplicate entry created by a bug) — not as part of routine
    operations, or the ledger stops meaning anything.
    """

    list_display = (
        "id",
        "wallet",
        "entry_type",
        "amount",
        "balance_after_available",
        "balance_after_locked",
        "created_at",
    )
    list_filter = ("entry_type",)
    search_fields = ("wallet__user__email", "reference")
    ordering = ("-created_at",)
    readonly_fields = ("id",)