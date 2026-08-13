from rest_framework import serializers

from .models import Wallet, WalletLedgerEntry


class WalletSerializer(serializers.ModelSerializer):
    total_balance = serializers.DecimalField(
        max_digits=18, decimal_places=2, read_only=True,
        help_text="Computed: available_balance + locked_balance.",
    )

    class Meta:
        model = Wallet
        fields = [
            "available_balance",
            "locked_balance",
            "total_balance",
            "total_deposited",
            "total_withdrawn",
            "total_profit_earned",
            "updated_at",
        ]
        read_only_fields = fields


class WalletLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletLedgerEntry
        fields = [
            "entry_type",
            "amount",
            "balance_after_available",
            "balance_after_locked",
            "reference",
            "created_at",
        ]
        read_only_fields = fields