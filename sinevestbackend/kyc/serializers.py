from rest_framework import serializers

from .models import KYCProfile


class PersonalAndAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = [
            "date_of_birth", "gender", "nationality", "phone_number",
            "country", "state", "city", "street_address", "postal_code",
        ]


class EmploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = [
            "employment_status", "employer_name", "occupation",
            "annual_income_range", "source_of_funds",
        ]


class GovernmentIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = ["id_type", "id_number", "id_issuing_country", "id_expiry_date"]


class TradingExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = [
            "trading_experience_level", "years_of_trading_experience",
            "risk_tolerance", "preferred_markets",
        ]


class ComplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = ["is_politically_exposed_person", "agreed_to_terms"]


class KYCProfileReadSerializer(serializers.ModelSerializer):
    """
    Read-only, nested-by-section representation used for GET /api/kyc/ and
    as the response shape after a successful PATCH.
    """

    personal_and_address = serializers.SerializerMethodField()
    employment = serializers.SerializerMethodField()
    government_id = serializers.SerializerMethodField()
    trading_expertise = serializers.SerializerMethodField()
    compliance = serializers.SerializerMethodField()

    class Meta:
        model = KYCProfile
        fields = [
            "status", "submitted_at", "reviewed_at", "admin_notes",
            "personal_and_address", "employment", "government_id",
            "trading_expertise", "compliance",
        ]

    def get_personal_and_address(self, obj):
        return PersonalAndAddressSerializer(obj).data

    def get_employment(self, obj):
        return EmploymentSerializer(obj).data

    def get_government_id(self, obj):
        return GovernmentIDSerializer(obj).data

    def get_trading_expertise(self, obj):
        return TradingExpertiseSerializer(obj).data

    def get_compliance(self, obj):
        return ComplianceSerializer(obj).data


class KYCProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Flat, partial-update serializer accepting any subset of KYC fields
    (matching the model field names directly, as recommended by the spec).
    System fields (status, admin_notes, submitted_at, reviewed_at) are
    read-only here — they're managed by the submit endpoint and Django admin.
    """

    class Meta:
        model = KYCProfile
        fields = [
            "date_of_birth", "gender", "nationality", "phone_number",
            "country", "state", "city", "street_address", "postal_code",
            "employment_status", "employer_name", "occupation",
            "annual_income_range", "source_of_funds",
            "id_type", "id_number", "id_issuing_country", "id_expiry_date",
            "trading_experience_level", "years_of_trading_experience",
            "risk_tolerance", "preferred_markets",
            "is_politically_exposed_person", "agreed_to_terms",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}


class KYCSubmitResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = ["status", "submitted_at"]


class KYCStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCProfile
        fields = ["status", "submitted_at", "reviewed_at"]


class KYCCompletionSectionsSerializer(serializers.Serializer):
    personal_and_address = serializers.IntegerField()
    employment = serializers.IntegerField()
    government_id = serializers.IntegerField()
    trading_expertise = serializers.IntegerField()
    compliance = serializers.IntegerField()


class KYCCompletionSerializer(serializers.Serializer):
    overall_percentage = serializers.IntegerField()
    sections = KYCCompletionSectionsSerializer()


# ---------------------------------------------------------------------------
# Docs-only serializers — exist purely so drf-spectacular can render accurate
# Swagger/Redoc schemas for response shapes that don't map to a single
# ModelSerializer (a combined message+data body, or a generic error shape).
# ---------------------------------------------------------------------------


class ErrorDetailSerializer(serializers.Serializer):
    """Docs-only: generic {"detail": "..."} error response shape, reused across several endpoints."""

    detail = serializers.CharField()


class KYCSubmitFullResponseSerializer(serializers.Serializer):
    """Docs-only: shape of the 200 response from POST /api/kyc/submit/ (message + status + submitted_at)."""

    message = serializers.CharField()
    status = serializers.CharField()
    submitted_at = serializers.DateTimeField()