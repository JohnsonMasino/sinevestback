from django.apps import AppConfig


class TransactionPinConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transaction_pin"

    def ready(self):
        import transaction_pin.signals  # noqa: F401