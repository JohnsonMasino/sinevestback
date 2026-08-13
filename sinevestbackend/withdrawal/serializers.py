from decimal import Decimal

from django.conf import settings
from rest_framework import serializers

from transaction_pin.services import verify_pin

from .models import Withdrawal
from .services import get_valid_otp, pending_amount_total


def _min_withdrawal_amount() -> Decimal:
    return Decimal(str(getattr(settings, "MIN_WITHDRAWAL_AMOUNT", "2.00")))


def _looks_like_trc20_address(value: str) -> bool:
    """
    Basic format check only — not a full checksum validation.
    TRC20 addresses start with 'T' and are 34 characters, base58.
    """
    if not value:
        return False
    return value.startswith("T") and 25 <= len(value) <= 42 and value.isalnum()


class WithdrawalInitiateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, help_text="Amount to withdraw in USD.")
    wallet_address = serializers.CharField(
        max_length=255, help_text="Destination USDT-TRC20 wallet address."
    )
    transaction_pin = serializers.CharField(
        max_length=4, min_length=4, write_only=True, help_text="Your 4-digit transaction PIN."
    )

    def validate_amount(self, value):
        min_amount = _min_withdrawal_amount()
        if value < min_amount:
            raise serializers.ValidationError(f"Minimum withdrawal amount is ${min_amount}.")
        return value

    def validate_wallet_address(self, value):
        if not _looks_like_trc20_address(value):
            raise serializers.ValidationError("This does not look like a valid USDT-TRC20 address.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        wallet = user.wallet

        already_pending = pending_amount_total(user)
        if already_pending + attrs["amount"] > wallet.available_balance:
            raise serializers.ValidationError(
                {"amount": ["Amount exceeds your available balance."]}
            )

        if not verify_pin(user, attrs["transaction_pin"]):
            raise serializers.ValidationError(
                {"transaction_pin": ["Incorrect transaction PIN."]}
            )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data.pop("transaction_pin", None)
        return Withdrawal.objects.create(
            user=user,
            amount=validated_data["amount"],
            wallet_address=validated_data["wallet_address"],
            status=Withdrawal.Status.PENDING_OTP,
        )


class WithdrawalConfirmSerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6, min_length=6, help_text="6-digit OTP sent to the user's email.")

    def validate(self, attrs):
        withdrawal = self.context["withdrawal"]
        otp = get_valid_otp(withdrawal, attrs["otp_code"])
        if not otp:
            raise serializers.ValidationError({"otp_code": ["Invalid or expired OTP."]})
        attrs["otp"] = otp
        return attrs


class WithdrawalSerializer(serializers.ModelSerializer):
    """Used for list/detail responses."""

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "amount",
            "wallet_address",
            "network",
            "status",
            "admin_notes",
            "created_at",
            "processed_at",
        ]
        read_only_fields = fields