"""
Pure query/serialization logic. No models live here — this app is a
read-only aggregator over deposit.Deposit, withdrawal.Withdrawal, and
trade.Trade, per the app's design (avoids a second, potentially-drifting
source of truth).
"""
from deposit.models import Deposit
from trade.models import Trade
from withdrawal.models import Withdrawal

VALID_TYPES = {"deposit", "withdrawal", "trade"}


def _serialize_deposit(deposit: Deposit) -> dict:
    return {
        "id": str(deposit.id),
        "type": "deposit",
        "amount": str(deposit.amount),
        "status": deposit.status,
        "description": "Deposit request",
        "created_at": deposit.created_at,
        "resolved_at": deposit.processed_at,
    }


def _serialize_withdrawal(withdrawal: Withdrawal) -> dict:
    return {
        "id": str(withdrawal.id),
        "type": "withdrawal",
        "amount": str(withdrawal.amount),
        "status": withdrawal.status,
        "description": f"Withdrawal to {withdrawal.wallet_address[:6]}...",
        "created_at": withdrawal.created_at,
        "resolved_at": withdrawal.processed_at,
    }


def _serialize_trade(trade: Trade) -> dict:
    return {
        "id": str(trade.id),
        "type": "trade",
        "amount": str(trade.amount),
        "status": trade.status,
        "description": f"{trade.plan.name} investment",
        "created_at": trade.started_at,
        "resolved_at": trade.closed_at,
    }


def get_deposits_queryset(user):
    return Deposit.objects.filter(user=user)


def get_withdrawals_queryset(user):
    # pending_otp withdrawals aren't confirmed requests yet and may still
    # be auto-deleted by the cron cleanup job — never surface them here.
    return Withdrawal.objects.filter(user=user).exclude(status=Withdrawal.Status.PENDING_OTP)


def get_trades_queryset(user):
    return Trade.objects.filter(user=user).select_related("plan")


def get_unified_transactions(
    user,
    *,
    type_filter: str | None = None,
    status_filter: str | None = None,
    date_from=None,
    date_to=None,
) -> list[dict]:
    """
    Builds the merged, sorted (newest-first) list of unified transaction
    dicts for a user, optionally narrowed by type/status/date range.

    date_from / date_to are expected to already be parsed `date` objects
    (or None) — see views.py for the ISO-string parsing at the request layer.
    """
    entries: list[dict] = []

    if type_filter in (None, "deposit"):
        entries.extend(_serialize_deposit(d) for d in get_deposits_queryset(user))
    if type_filter in (None, "withdrawal"):
        entries.extend(_serialize_withdrawal(w) for w in get_withdrawals_queryset(user))
    if type_filter in (None, "trade"):
        entries.extend(_serialize_trade(t) for t in get_trades_queryset(user))

    if status_filter:
        entries = [e for e in entries if e["status"] == status_filter]

    if date_from:
        entries = [e for e in entries if e["created_at"].date() >= date_from]
    if date_to:
        entries = [e for e in entries if e["created_at"].date() <= date_to]

    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return entries


def get_summary(user) -> dict:
    from decimal import Decimal

    from django.db.models import Sum

    deposits = get_deposits_queryset(user)
    withdrawals = get_withdrawals_queryset(user)
    trades = get_trades_queryset(user)

    deposits_total_approved = (
        deposits.filter(status="approved").aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    )
    withdrawals_total_completed = (
        withdrawals.filter(status=Withdrawal.Status.COMPLETED).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    trades_total_profit = (
        trades.filter(status=Trade.Status.COMPLETED).aggregate(total=Sum("actual_profit_paid"))["total"]
        or Decimal("0.00")
    )

    return {
        "deposits": {
            "count": deposits.count(),
            "total_approved": str(deposits_total_approved),
        },
        "withdrawals": {
            "count": withdrawals.count(),
            "total_completed": str(withdrawals_total_completed),
        },
        "trades": {
            "count": trades.count(),
            "active_count": trades.filter(status=Trade.Status.ACTIVE).count(),
            "completed_count": trades.filter(status=Trade.Status.COMPLETED).count(),
            "total_profit_earned": str(trades_total_profit),
        },
    }