from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Trade, TradePlan


class TradePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePlan
        fields = ["code", "name", "min_amount", "max_amount", "profit_percentage", "duration_hours"]
        read_only_fields = fields


class TradeCreateSerializer(serializers.Serializer):
    plan_code = serializers.CharField(help_text="One of: silver, gold, forex, company_shares, real_estate.")
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, help_text="Principal to lock into this trade.")

    def validate(self, attrs):
        try:
            plan = TradePlan.objects.get(code=attrs["plan_code"], is_active=True)
        except TradePlan.DoesNotExist:
            raise serializers.ValidationError({"plan_code": ["This plan does not exist or is not currently active."]})

        amount = attrs["amount"]

        if amount < plan.min_amount:
            raise serializers.ValidationError(
                {"amount": [self._range_message(plan)]}
            )
        if plan.max_amount is not None and amount > plan.max_amount:
            raise serializers.ValidationError(
                {"amount": [self._range_message(plan)]}
            )

        user = self.context["request"].user
        wallet = user.wallet
        if amount > wallet.available_balance:
            raise serializers.ValidationError({"amount": ["Amount exceeds your available wallet balance."]})

        attrs["plan"] = plan
        return attrs

    @staticmethod
    def _range_message(plan: TradePlan) -> str:
        if plan.max_amount is not None:
            return f"Amount must be between ${plan.min_amount} and ${plan.max_amount} for the {plan.name}."
        return f"Amount must be at least ${plan.min_amount} for the {plan.name}."

    def create(self, validated_data):
        from django.db import transaction

        from wallet.services import lock_funds

        user = self.context["request"].user
        plan: TradePlan = validated_data["plan"]
        amount: Decimal = validated_data["amount"]

        expected_profit = (amount * plan.profit_percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        matures_at = timezone.now() + timezone.timedelta(hours=plan.duration_hours)

        with transaction.atomic():
            lock_funds(user.wallet, amount, reason=f"Trade lock - {plan.name}")
            trade = Trade.objects.create(
                user=user,
                plan=plan,
                amount=amount,
                profit_percentage=plan.profit_percentage,
                duration_hours=plan.duration_hours,
                expected_profit=expected_profit,
                matures_at=matures_at,
            )
        return trade


class TradeCreateResponseSerializer(serializers.ModelSerializer):
    plan_code = serializers.CharField(source="plan.code")
    plan_name = serializers.CharField(source="plan.name")

    class Meta:
        model = Trade
        fields = [
            "id",
            "plan_code",
            "plan_name",
            "amount",
            "profit_percentage",
            "expected_profit",
            "duration_hours",
            "status",
            "started_at",
            "matures_at",
        ]
        read_only_fields = fields


class ActiveTradeSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name")
    time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = ["id", "plan_name", "amount", "expected_profit", "matures_at", "time_remaining_seconds"]
        read_only_fields = fields

    def get_time_remaining_seconds(self, obj: Trade) -> int:
        remaining = (obj.matures_at - timezone.now()).total_seconds()
        return max(0, int(remaining))


class TradeHistorySerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name")

    class Meta:
        model = Trade
        fields = [
            "id",
            "plan_name",
            "amount",
            "profit_percentage",
            "expected_profit",
            "actual_profit_paid",
            "status",
            "started_at",
            "matures_at",
            "closed_at",
        ]
        read_only_fields = fields


class TradeDetailSerializer(TradeHistorySerializer):
    plan_code = serializers.CharField(source="plan.code")

    class Meta(TradeHistorySerializer.Meta):
        fields = ["plan_code"] + TradeHistorySerializer.Meta.fields


class CronCloseExpiredTradesResponseSerializer(serializers.Serializer):
    """Docs-only: shape of the 200 response from /cron/close-expired-trades/."""

    trades_closed = serializers.IntegerField()
    trade_ids = serializers.ListField(child=serializers.UUIDField())


class CronCleanupResponseSerializer(serializers.Serializer):
    """Docs-only: shape of the 200 response from /cron/cleanup-pending-transactions/."""

    withdrawals_deleted = serializers.IntegerField()
    deposits_deleted = serializers.IntegerField()