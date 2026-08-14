"""
These serializers are not used to build the response data (services.py
returns plain dicts, since the unified shape doesn't map 1:1 to any single
model). They exist purely so drf-spectacular/drf-yasg can render accurate
Swagger/Redoc schemas for these endpoints, per the project's docs rule.
"""
from rest_framework import serializers


class UnifiedTransactionSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="UUID of the underlying deposit, withdrawal, or trade record.")
    type = serializers.ChoiceField(
        choices=["deposit", "withdrawal", "trade"],
        help_text="Which source app this entry came from.",
    )
    amount = serializers.CharField(help_text="Decimal amount as a string, e.g. '500.00'.")
    status = serializers.CharField(
        help_text="pending | approved | rejected | completed | active | cancelled, depending on type."
    )
    description = serializers.CharField(help_text="Human-readable summary, e.g. 'Gold Plan investment'.")
    created_at = serializers.DateTimeField(help_text="When the underlying request/trade was created.")
    resolved_at = serializers.DateTimeField(
        allow_null=True, help_text="When it was approved/rejected/closed, or null if still open."
    )


class DepositSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    total_approved = serializers.CharField()


class WithdrawalSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    total_completed = serializers.CharField()


class TradeSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    total_profit_earned = serializers.CharField()


class TransactionSummarySerializer(serializers.Serializer):
    deposits = DepositSummarySerializer()
    withdrawals = WithdrawalSummarySerializer()
    trades = TradeSummarySerializer()