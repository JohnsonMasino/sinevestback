import uuid

from django.conf import settings
from django.db import models


class KYCProfile(models.Model):
    """
    One profile per user, split logically into sections (personal & address,
    employment, government id, trading expertise, compliance) even though
    it's a single flat table. The serializer nests these into groups for
    the frontend. Not required for deposits/trades — purely status display.
    """

    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )
    EMPLOYMENT_STATUS_CHOICES = (
        ("employed", "Employed"),
        ("self_employed", "Self-Employed"),
        ("unemployed", "Unemployed"),
        ("student", "Student"),
        ("retired", "Retired"),
    )
    INCOME_RANGE_CHOICES = (
        ("under_10k", "Under $10,000"),
        ("10k_50k", "$10,000 - $50,000"),
        ("50k_100k", "$50,000 - $100,000"),
        ("100k_500k", "$100,000 - $500,000"),
        ("above_500k", "Above $500,000"),
    )
    SOURCE_OF_FUNDS_CHOICES = (
        ("salary", "Salary"),
        ("business_income", "Business Income"),
        ("investments", "Investments"),
        ("inheritance", "Inheritance"),
        ("other", "Other"),
    )
    ID_TYPE_CHOICES = (
        ("passport", "Passport"),
        ("national_id", "National ID"),
        ("drivers_license", "Driver's License"),
        ("voters_card", "Voter's Card"),
    )
    TRADING_EXPERIENCE_CHOICES = (
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
        ("professional", "Professional"),
    )
    RISK_TOLERANCE_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    )
    STATUS_CHOICES = (
        ("not_submitted", "Not Submitted"),
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="kyc_profile",
        help_text="The user this KYC profile belongs to.",
    )

    # --- Personal & Address ---
    date_of_birth = models.DateField(null=True, blank=True, help_text="User's date of birth.")
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, null=True, blank=True,
        help_text="One of: male, female, other.",
    )
    nationality = models.CharField(max_length=100, null=True, blank=True, help_text="User's nationality.")
    phone_number = models.CharField(max_length=20, null=True, blank=True, help_text="Contact phone number.")
    country = models.CharField(max_length=100, null=True, blank=True, help_text="Country of residence.")
    state = models.CharField(max_length=100, null=True, blank=True, help_text="State/region of residence.")
    city = models.CharField(max_length=100, null=True, blank=True, help_text="City of residence.")
    street_address = models.CharField(max_length=255, null=True, blank=True, help_text="Street address.")
    postal_code = models.CharField(max_length=20, null=True, blank=True, help_text="Postal/ZIP code.")

    # --- Employment ---
    employment_status = models.CharField(
        max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, null=True, blank=True,
        help_text="One of: employed, self_employed, unemployed, student, retired.",
    )
    employer_name = models.CharField(max_length=150, blank=True, help_text="Name of current employer, if any.")
    occupation = models.CharField(max_length=150, blank=True, help_text="Current occupation/job title.")
    annual_income_range = models.CharField(
        max_length=20, choices=INCOME_RANGE_CHOICES, null=True, blank=True,
        help_text="One of: under_10k, 10k_50k, 50k_100k, 100k_500k, above_500k.",
    )
    source_of_funds = models.CharField(
        max_length=20, choices=SOURCE_OF_FUNDS_CHOICES, null=True, blank=True,
        help_text="One of: salary, business_income, investments, inheritance, other.",
    )

    # --- Government ID ---
    id_type = models.CharField(
        max_length=20, choices=ID_TYPE_CHOICES, null=True, blank=True,
        help_text="One of: passport, national_id, drivers_license, voters_card.",
    )
    id_number = models.CharField(max_length=100, null=True, blank=True, help_text="Government ID number.")
    id_issuing_country = models.CharField(
        max_length=100, null=True, blank=True, help_text="Country that issued the ID."
    )
    id_expiry_date = models.DateField(null=True, blank=True, help_text="Expiry date of the government ID.")

    # --- Trading Expertise ---
    trading_experience_level = models.CharField(
        max_length=20, choices=TRADING_EXPERIENCE_CHOICES, null=True, blank=True,
        help_text="One of: beginner, intermediate, advanced, professional.",
    )
    years_of_trading_experience = models.PositiveIntegerField(
        null=True, blank=True, help_text="Number of years of trading experience."
    )
    risk_tolerance = models.CharField(
        max_length=10, choices=RISK_TOLERANCE_CHOICES, null=True, blank=True,
        help_text="One of: low, medium, high.",
    )
    preferred_markets = models.CharField(
        max_length=255, blank=True,
        help_text="Free-text/comma-separated list of preferred markets, e.g. 'forex, shares'.",
    )

    # --- Compliance & Professional ---
    is_politically_exposed_person = models.BooleanField(
        default=False, help_text="Whether the user is a politically exposed person (PEP)."
    )
    agreed_to_terms = models.BooleanField(
        default=False, help_text="Whether the user has agreed to the KYC terms. Required to submit."
    )

    # --- System ---
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_submitted",
        help_text="One of: not_submitted, pending, approved, rejected.",
    )
    admin_notes = models.TextField(
        blank=True, help_text="Internal admin-only notes, e.g. reason for rejection."
    )
    submitted_at = models.DateTimeField(null=True, blank=True, help_text="Set automatically when the user submits.")
    reviewed_at = models.DateTimeField(
        null=True, blank=True, help_text="Set automatically when an admin approves or rejects. Never manually editable."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "KYC Profile"
        verbose_name_plural = "KYC Profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.status}"

    @property
    def is_editable(self):
        """Users may only edit their KYC data while it's a draft or was rejected."""
        return self.status in ("not_submitted", "rejected")