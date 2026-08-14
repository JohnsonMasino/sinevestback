import uuid
from django.conf import settings
from django.db import models


class TradePlan(models.Model):
    code = models.CharField(
        max_length=30,
        primary_key=True,
        help_text="Fixed plan code, e.g. 'silver', 'gold'. Seeded via migration, not user-created.",
    )
    name = models.CharField(max_length=100, help_text="Display name, e.g. 'Silver Plan'.")
    min_amount = models.DecimalField(max_digits=18, decimal_places=2, help_text="Minimum trade amount for this plan.")
    max_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum trade amount. Null means unlimited (Real Estate plan).",
    )
    profit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Fixed simulated return, e.g. 20.00 for 20%.",
    )
    duration_hours = models.PositiveIntegerField(help_text="How long a trade opened on this plan runs, in hours.")
    is_active = models.BooleanField(
        default=True,
        help_text="Admin can disable a plan without deleting it; disabled plans reject new trades.",
    )

    class Meta:
        db_table = "trade_tradeplan"
        ordering = ["min_amount"]

    def __str__(self):
        return self.name


class Trade(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trades",
    )
    plan = models.ForeignKey(
        TradePlan,
        on_delete=models.PROTECT,
        related_name="trades",
    )

    amount = models.DecimalField(max_digits=18, decimal_places=2, help_text="Principal locked for this trade.")

    # Snapshotted from the plan at creation time so later admin edits to the
    # plan never retroactively change an in-flight or historical trade.
    profit_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    duration_hours = models.PositiveIntegerField()
    expected_profit = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        help_text="amount * profit_percentage / 100, computed and stored at creation.",
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    started_at = models.DateTimeField(auto_now_add=True)
    matures_at = models.DateTimeField(help_text="started_at + duration_hours, computed at creation.")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="Set automatically by the cron closure job.")
    actual_profit_paid = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Set when closed. Equals expected_profit in this simulation.",
    )

    class Meta:
        db_table = "trade_trade"
        ordering = ["-started_at"]

    def __str__(self):
        return f"Trade({self.id}, user={self.user_id}, plan={self.plan_id}, status={self.status})"