from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """
    Same pattern as Wallet/KYCProfile/TransactionPin: every new User
    automatically gets a Profile row with all optional fields blank/null,
    so GET /api/profile/ never 404s.
    """
    if created:
        Profile.objects.get_or_create(user=instance)