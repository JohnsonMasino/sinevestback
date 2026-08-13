from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .emails import send_account_disabled_email

User = get_user_model()


@receiver(pre_save, sender=User)
def handle_is_active_change(sender, instance, **kwargs):
    """
    Fires send_account_disabled_email whenever an existing user's is_active
    transitions from True to False (e.g. an admin disabling the account from
    the Django admin).
    """
    if not instance.pk:
        return  # new user being created, nothing to compare against

    try:
        previous = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return

    if previous.is_active and not instance.is_active:
        send_account_disabled_email(instance)