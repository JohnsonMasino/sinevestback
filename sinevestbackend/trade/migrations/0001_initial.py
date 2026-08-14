import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TradePlan",
            fields=[
                (
                    "code",
                    models.CharField(
                        help_text="Fixed plan code, e.g. 'silver', 'gold'. Seeded via migration, not user-created.",
                        max_length=30,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(help_text="Display name, e.g. 'Silver Plan'.", max_length=100)),
                (
                    "min_amount",
                    models.DecimalField(
                        decimal_places=2, help_text="Minimum trade amount for this plan.", max_digits=18
                    ),
                ),
                (
                    "max_amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Maximum trade amount. Null means unlimited (Real Estate plan).",
                        max_digits=18,
                        null=True,
                    ),
                ),
                (
                    "profit_percentage",
                    models.DecimalField(
                        decimal_places=2, help_text="Fixed simulated return, e.g. 20.00 for 20%.", max_digits=5
                    ),
                ),
                (
                    "duration_hours",
                    models.PositiveIntegerField(
                        help_text="How long a trade opened on this plan runs, in hours."
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Admin can disable a plan without deleting it; disabled plans reject new trades.",
                    ),
                ),
            ],
            options={
                "db_table": "trade_tradeplan",
                "ordering": ["min_amount"],
            },
        ),
        migrations.CreateModel(
            name="Trade",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount", models.DecimalField(decimal_places=2, help_text="Principal locked for this trade.", max_digits=18)),
                ("profit_percentage", models.DecimalField(decimal_places=2, max_digits=5)),
                ("duration_hours", models.PositiveIntegerField()),
                (
                    "expected_profit",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="amount * profit_percentage / 100, computed and stored at creation.",
                        max_digits=18,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("completed", "Completed"), ("cancelled", "Cancelled")],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                (
                    "matures_at",
                    models.DateTimeField(help_text="started_at + duration_hours, computed at creation."),
                ),
                (
                    "closed_at",
                    models.DateTimeField(
                        blank=True, help_text="Set automatically by the cron closure job.", null=True
                    ),
                ),
                (
                    "actual_profit_paid",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Set when closed. Equals expected_profit in this simulation.",
                        max_digits=18,
                        null=True,
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="trades", to="trade.tradeplan"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trades",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "trade_trade",
                "ordering": ["-started_at"],
            },
        ),
    ]