from django.db import models

# Section -> ordered list of model field names counted toward completion.
# System fields (user, status, admin_notes, submitted_at, reviewed_at,
# created_at, updated_at, id) are intentionally excluded.
FIELD_SECTIONS = {
    "personal_and_address": [
        "date_of_birth",
        "gender",
        "nationality",
        "phone_number",
        "country",
        "state",
        "city",
        "street_address",
        "postal_code",
    ],
    "employment": [
        "employment_status",
        "employer_name",
        "occupation",
        "annual_income_range",
        "source_of_funds",
    ],
    "government_id": [
        "id_type",
        "id_number",
        "id_issuing_country",
        "id_expiry_date",
    ],
    "trading_expertise": [
        "trading_experience_level",
        "years_of_trading_experience",
        "risk_tolerance",
        "preferred_markets",
    ],
    "compliance": [
        "is_politically_exposed_person",
        "agreed_to_terms",
    ],
}


def _is_field_filled(instance, field_name: str) -> bool:
    """
    A field counts as "filled" if it carries real information:
    - BooleanField: counts as filled only when True (an unanswered compliance
      checkbox defaults to False, which shouldn't read as "complete").
    - Everything else: filled when not None and, for strings, not blank.
    """
    field = instance._meta.get_field(field_name)
    value = getattr(instance, field_name)

    if isinstance(field, models.BooleanField):
        return bool(value)

    if value is None:
        return False

    if isinstance(value, str) and value.strip() == "":
        return False

    return True


def compute_kyc_completion(profile) -> tuple[int, dict]:
    """
    Returns (overall_percentage, {section_name: section_percentage}).
    Independent of `status` — purely a measure of how much data is filled in.
    """
    section_percentages = {}
    total_fields = 0
    total_filled = 0

    for section_name, field_names in FIELD_SECTIONS.items():
        filled_count = sum(1 for f in field_names if _is_field_filled(profile, f))
        section_percentages[section_name] = (
            round((filled_count / len(field_names)) * 100) if field_names else 0
        )
        total_fields += len(field_names)
        total_filled += filled_count

    overall_percentage = round((total_filled / total_fields) * 100) if total_fields else 0
    return overall_percentage, section_percentages