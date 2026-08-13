from django.contrib import admin
from django.utils import timezone

from .emails import send_kyc_approved_email, send_kyc_rejected_email
from .models import KYCProfile


@admin.register(KYCProfile)
class KYCProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "submitted_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("user__email",)
    readonly_fields = ("id", "reviewed_at", "created_at", "updated_at")
    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Personal & Address",
            {
                "fields": (
                    "date_of_birth", "gender", "nationality", "phone_number",
                    "country", "state", "city", "street_address", "postal_code",
                )
            },
        ),
        (
            "Employment",
            {
                "fields": (
                    "employment_status", "employer_name", "occupation",
                    "annual_income_range", "source_of_funds",
                )
            },
        ),
        (
            "Government ID",
            {"fields": ("id_type", "id_number", "id_issuing_country", "id_expiry_date")},
        ),
        (
            "Trading Expertise",
            {
                "fields": (
                    "trading_experience_level", "years_of_trading_experience",
                    "risk_tolerance", "preferred_markets",
                )
            },
        ),
        (
            "Compliance & Professional",
            {"fields": ("is_politically_exposed_person", "agreed_to_terms")},
        ),
        (
            "Review",
            {"fields": ("status", "admin_notes", "submitted_at", "reviewed_at")},
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Detects a transition into approved/rejected and:
        - stamps reviewed_at = timezone.now() (never manually editable)
        - fires the matching notification email
        """
        previous_status = None
        if change and obj.pk:
            previous_status = KYCProfile.objects.filter(pk=obj.pk).values_list("status", flat=True).first()

        status_changed_to_reviewed = (
            obj.status in ("approved", "rejected") and obj.status != previous_status
        )

        if status_changed_to_reviewed:
            obj.reviewed_at = timezone.now()

        super().save_model(request, obj, form, change)

        if status_changed_to_reviewed:
            if obj.status == "approved":
                send_kyc_approved_email(obj.user)
            elif obj.status == "rejected":
                send_kyc_rejected_email(obj.user, reason=obj.admin_notes)