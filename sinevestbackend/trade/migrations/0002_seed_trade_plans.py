from django.db import migrations


PLANS = [
    {
        "code": "silver",
        "name": "Silver Plan",
        "min_amount": "200.00",
        "max_amount": "499.00",
        "profit_percentage": "20.00",
        "duration_hours": 24,
    },
    {
        "code": "gold",
        "name": "Gold Plan",
        "min_amount": "500.00",
        "max_amount": "999.00",
        "profit_percentage": "17.50",
        "duration_hours": 48,
    },
    {
        "code": "forex",
        "name": "Forex Plan",
        "min_amount": "1000.00",
        "max_amount": "1999.00",
        "profit_percentage": "20.00",
        "duration_hours": 96,
    },
    {
        "code": "company_shares",
        "name": "Company Shares",
        "min_amount": "2000.00",
        "max_amount": "3999.00",
        "profit_percentage": "40.00",
        "duration_hours": 120,
    },
    {
        "code": "real_estate",
        "name": "Real Estate",
        "min_amount": "4000.00",
        "max_amount": None,
        "profit_percentage": "75.00",
        "duration_hours": 168,
    },
]


def seed_plans(apps, schema_editor):
    TradePlan = apps.get_model("trade", "TradePlan")
    for plan in PLANS:
        TradePlan.objects.update_or_create(
            code=plan["code"],
            defaults={
                "name": plan["name"],
                "min_amount": plan["min_amount"],
                "max_amount": plan["max_amount"],
                "profit_percentage": plan["profit_percentage"],
                "duration_hours": plan["duration_hours"],
                "is_active": True,
            },
        )


def unseed_plans(apps, schema_editor):
    TradePlan = apps.get_model("trade", "TradePlan")
    TradePlan.objects.filter(code__in=[p["code"] for p in PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("trade", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_code=unseed_plans),
    ]