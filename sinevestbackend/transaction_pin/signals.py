from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import TransactionPin


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_transaction_pin_for_new_user(sender, instance, created, **kwargs):
    """
    Mirrors the Wallet/KYCProfile pattern: every new User automatically
    gets a TransactionPin row with is_set=False, so the frontend can
    always GET /api/transaction-pin/ safely without a 404.
    """
    if created:
        TransactionPin.objects.get_or_create(user=instance)