import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Deposit(models.Model):
    """
    A user's deposit request. Stays 'pending' with no wallet effect until an
    admin reviews it from the Django admin — approval credits the wallet via
    wallet.services.credit_available, rejection does not touch the wallet.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        help_text="Also serves as the human-visible deposit reference.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deposits",
        help_text="The user who requested this deposit.",
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=2, help_text="Deposit amount in USD. Must be above the configured minimum."
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending",
        help_text="One of: pending, approved, rejected.",
    )
    admin_notes = models.TextField(
        blank=True, help_text="Optional reason, shown to the user if the deposit is rejected."
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text=(
            "When the user submitted the request. Auto-set on creation, but "
            "editable afterward by an admin to correct/backdate/postdate for "
            "display purposes. The API only ever exposes this read-only."
        ),
    )
    processed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Auto-set the moment an admin approves/rejects, but freely editable afterward for corrections.",
    )

    class Meta:
        verbose_name = "Deposit"
        verbose_name_plural = "Deposits"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Deposit #{self.id} - {self.user.email} - {self.amount} ({self.status})"