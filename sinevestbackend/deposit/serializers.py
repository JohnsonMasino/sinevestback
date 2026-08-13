from decimal import Decimal

from django.conf import settings
from rest_framework import serializers

from .models import Deposit


def get_min_deposit_amount() -> Decimal:
    return Decimal(str(getattr(settings, "MIN_DEPOSIT_AMOUNT", "10.00")))


class DepositCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ["amount"]
        extra_kwargs = {
            "amount": {"help_text": "Deposit amount in USD. Must be at least the configured minimum."}
        }

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")

        min_amount = get_min_deposit_amount()
        if value < min_amount:
            raise serializers.ValidationError(f"Minimum deposit amount is ${min_amount}.")

        return value


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ["id", "amount", "status", "admin_notes", "created_at", "processed_at"]
        read_only_fields = fields