from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers

from .models import PinChangeOTP, TransactionPin
from .services import create_pin_change_otp, get_latest_valid_pin_change_otp


class MessageResponseSerializer(serializers.Serializer):
    """Generic {"message": "..."} response shape, used for docs only."""

    message = serializers.CharField()


def _validate_4_digit_pin(value, field_name="PIN"):
    if not value.isdigit() or len(value) != 4:
        raise serializers.ValidationError(f"{field_name} must be exactly 4 digits.")
    return value


class TransactionPinDetailSerializer(serializers.ModelSerializer):
    """Read-only. Never exposes pin_hash."""

    class Meta:
        model = TransactionPin
        fields = ["is_set", "created_at", "updated_at"]
        read_only_fields = fields


class PinCreateSerializer(serializers.Serializer):
    pin = serializers.CharField(
        max_length=4,
        min_length=4,
        help_text="A new 4-digit numeric transaction PIN.",
    )
    confirm_pin = serializers.CharField(
        max_length=4,
        min_length=4,
        help_text="Must match 'pin'.",
    )

    def validate_pin(self, value):
        return _validate_4_digit_pin(value, "PIN")

    def validate_confirm_pin(self, value):
        return _validate_4_digit_pin(value, "Confirm PIN")

    def validate(self, attrs):
        if attrs["pin"] != attrs["confirm_pin"]:
            raise serializers.ValidationError({"confirm_pin": ["PINs do not match."]})

        user = self.context["request"].user
        tp, _ = TransactionPin.objects.get_or_create(user=user)
        if tp.is_set:
            raise serializers.ValidationError(
                {"non_field_errors": ["A PIN is already set. Use the change flow instead."]}
            )
        attrs["transaction_pin"] = tp
        return attrs

    def save(self):
        tp = self.validated_data["transaction_pin"]
        tp.pin_hash = make_password(self.validated_data["pin"])
        tp.is_set = True
        tp.save(update_fields=["pin_hash", "is_set", "updated_at"])
        return tp


class PinChangeInitiateSerializer(serializers.Serializer):
    current_pin = serializers.CharField(max_length=4, min_length=4, help_text="The currently active 4-digit PIN.")
    new_pin = serializers.CharField(max_length=4, min_length=4, help_text="The desired new 4-digit PIN.")
    confirm_new_pin = serializers.CharField(max_length=4, min_length=4, help_text="Must match 'new_pin'.")

    def validate_current_pin(self, value):
        return _validate_4_digit_pin(value, "Current PIN")

    def validate_new_pin(self, value):
        return _validate_4_digit_pin(value, "New PIN")

    def validate_confirm_new_pin(self, value):
        return _validate_4_digit_pin(value, "Confirm new PIN")

    def validate(self, attrs):
        user = self.context["request"].user

        try:
            tp = user.transaction_pin
        except TransactionPin.DoesNotExist:
            raise serializers.ValidationError(
                {"non_field_errors": ["No PIN has been set yet. Use the create flow first."]}
            )

        if not tp.is_set:
            raise serializers.ValidationError(
                {"non_field_errors": ["No PIN has been set yet. Use the create flow first."]}
            )

        if not check_password(attrs["current_pin"], tp.pin_hash):
            raise serializers.ValidationError({"current_pin": ["Current PIN is incorrect."]})

        if attrs["new_pin"] != attrs["confirm_new_pin"]:
            raise serializers.ValidationError({"confirm_new_pin": ["New PINs do not match."]})

        if attrs["new_pin"] == attrs["current_pin"]:
            raise serializers.ValidationError(
                {"new_pin": ["New PIN must be different from the current PIN."]}
            )

        attrs["transaction_pin"] = tp
        return attrs

    def save(self):
        user = self.context["request"].user
        return create_pin_change_otp(user, self.validated_data["new_pin"])


class PinChangeConfirmSerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6, min_length=6, help_text="6-digit OTP sent to the user's email.")

    def validate(self, attrs):
        user = self.context["request"].user
        otp = get_latest_valid_pin_change_otp(user, attrs["otp_code"])
        if not otp:
            raise serializers.ValidationError({"otp_code": ["Invalid or expired OTP."]})
        attrs["otp"] = otp
        return attrs

    def save(self):
        otp: PinChangeOTP = self.validated_data["otp"]
        tp = TransactionPin.objects.get(user=otp.user)
        tp.pin_hash = otp.new_pin_hash
        tp.save(update_fields=["pin_hash", "updated_at"])
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        return tp