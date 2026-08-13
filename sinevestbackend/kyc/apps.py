from django.apps import AppConfig


class KycConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kyc"
    verbose_name = "KYC"

    def ready(self):
        import kyc.signals  # noqa: F401