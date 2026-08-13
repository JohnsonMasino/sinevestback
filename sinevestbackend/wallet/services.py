"""
The only sanctioned way to move money in or out of a Wallet. Every other app
(deposit, withdrawal, trade) must call these functions instead of writing to
Wallet fields directly, so every balance change is atomic, race-safe
(select_for_update), and ledgered.
"""

from decimal import Decimal

from django.db import transaction

from .exceptions import InsufficientFundsError
from .models import Wallet, WalletLedgerEntry


def _validate_positive_amount(amount: Decimal) -> None:
    if amount is None or amount <= 0:
        raise ValueError("amount must be a positive number.")


def credit_available(wallet: Wallet, amount: Decimal, *, reason: str) -> Wallet:
    """
    Increase available_balance and total_deposited. Used by deposit approval.
    Writes a `deposit_credit` ledger entry.
    """
    _validate_positive_amount(amount)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        wallet.available_balance += amount
        wallet.total_deposited += amount
        wallet.save(update_fields=["available_balance", "total_deposited", "updated_at"])

        WalletLedgerEntry.objects.create(
            wallet=wallet,
            entry_type="deposit_credit",
            amount=amount,
            balance_after_available=wallet.available_balance,
            balance_after_locked=wallet.locked_balance,
            reference=reason,
        )

    return wallet


def debit_available(wallet: Wallet, amount: Decimal, *, reason: str) -> Wallet:
    """
    Decrease available_balance and increase total_withdrawn. Used by
    withdrawal approval. Raises InsufficientFundsError if amount exceeds
    available_balance. Writes a `withdrawal_debit` ledger entry.
    """
    _validate_positive_amount(amount)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if amount > wallet.available_balance:
            raise InsufficientFundsError(
                f"Insufficient available balance: requested {amount}, "
                f"available {wallet.available_balance}."
            )

        wallet.available_balance -= amount
        wallet.total_withdrawn += amount
        wallet.save(update_fields=["available_balance", "total_withdrawn", "updated_at"])

        WalletLedgerEntry.objects.create(
            wallet=wallet,
            entry_type="withdrawal_debit",
            amount=amount,
            balance_after_available=wallet.available_balance,
            balance_after_locked=wallet.locked_balance,
            reference=reason,
        )

    return wallet


def lock_funds(wallet: Wallet, amount: Decimal, *, reason: str) -> Wallet:
    """
    Move `amount` from available_balance to locked_balance. Used when a
    trade is opened. Raises InsufficientFundsError if amount exceeds
    available_balance. Writes a `trade_lock` ledger entry.
    """
    _validate_positive_amount(amount)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if amount > wallet.available_balance:
            raise InsufficientFundsError(
                f"Insufficient available balance to lock: requested {amount}, "
                f"available {wallet.available_balance}."
            )

        wallet.available_balance -= amount
        wallet.locked_balance += amount
        wallet.save(update_fields=["available_balance", "locked_balance", "updated_at"])

        WalletLedgerEntry.objects.create(
            wallet=wallet,
            entry_type="trade_lock",
            amount=amount,
            balance_after_available=wallet.available_balance,
            balance_after_locked=wallet.locked_balance,
            reference=reason,
        )

    return wallet


def unlock_and_credit(wallet: Wallet, principal: Decimal, profit: Decimal, *, reason: str) -> Wallet:
    """
    Called when a trade closes: subtract `principal` from locked_balance, add
    (principal + profit) to available_balance, add `profit` to
    total_profit_earned. Used by the trade app's cron closure job. Writes a
    `trade_unlock_credit` ledger entry for the full (principal + profit)
    amount credited back.
    """
    _validate_positive_amount(principal)
    if profit is None or profit < 0:
        raise ValueError("profit must be zero or a positive number.")

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if principal > wallet.locked_balance:
            raise InsufficientFundsError(
                f"Cannot unlock {principal}: only {wallet.locked_balance} is locked."
            )

        total_credit = principal + profit
        wallet.locked_balance -= principal
        wallet.available_balance += total_credit
        wallet.total_profit_earned += profit
        wallet.save(
            update_fields=["locked_balance", "available_balance", "total_profit_earned", "updated_at"]
        )

        WalletLedgerEntry.objects.create(
            wallet=wallet,
            entry_type="trade_unlock_credit",
            amount=total_credit,
            balance_after_available=wallet.available_balance,
            balance_after_locked=wallet.locked_balance,
            reference=reason,
        )

    return wallet