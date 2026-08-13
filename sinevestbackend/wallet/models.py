import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    """
    Holds each user's simulated USD balance. Never mutated directly outside
    wallet/services.py — deposit, withdrawal, and trade all go through those
    functions so every balance change is ledgered and auditable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
        help_text="The user this wallet belongs to.",
    )
    available_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00"),
        help_text="Funds the user can withdraw or invest right now.",
    )
    locked_balance = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00"),
        help_text="Funds currently tied up in active trades.",
    )
    total_deposited = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00"),
        help_text="Running lifetime total of approved deposits (display stat).",
    )
    total_withdrawn = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00"),
        help_text="Running lifetime total of approved withdrawals (display stat).",
    )
    total_profit_earned = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0.00"),
        help_text="Running lifetime total of trade profits credited (display stat).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"

    def __str__(self):
        return f"{self.user.email} - wallet"

    @property
    def total_balance(self) -> Decimal:
        """Computed, never stored: available_balance + locked_balance."""
        return self.available_balance + self.locked_balance


class WalletLedgerEntry(models.Model):
    """
    Append-only audit log. Every balance movement made through
    wallet/services.py writes one of these — this is the system of record
    instead of ever allowing a raw balance edit.
    """

    ENTRY_TYPE_CHOICES = (
        ("deposit_credit", "Deposit Credit"),
        ("withdrawal_debit", "Withdrawal Debit"),
        ("trade_lock", "Trade Lock"),
        ("trade_unlock_credit", "Trade Unlock Credit"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="ledger_entries",
        help_text="The wallet this entry belongs to.",
    )
    entry_type = models.CharField(
        max_length=30, choices=ENTRY_TYPE_CHOICES,
        help_text="One of: deposit_credit, withdrawal_debit, trade_lock, trade_unlock_credit.",
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2,
        help_text="Always positive; direction is implied by entry_type.",
    )
    balance_after_available = models.DecimalField(
        max_digits=18, decimal_places=2, help_text="Snapshot of available_balance after this entry."
    )
    balance_after_locked = models.DecimalField(
        max_digits=18, decimal_places=2, help_text="Snapshot of locked_balance after this entry."
    )
    reference = models.CharField(
        max_length=255, blank=True, help_text="e.g. 'Deposit #123', 'Trade #45 payout'."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Wallet Ledger Entry"
        verbose_name_plural = "Wallet Ledger Entries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.wallet.user.email} - {self.entry_type} - {self.amount}"