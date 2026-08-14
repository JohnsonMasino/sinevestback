from django.conf import settings


def is_valid_cron_secret(request) -> bool:
    """
    Shared-secret check for cron-triggered endpoints. cronjob.org calls
    these without any user session, so this is intentionally the ONLY
    gate on them (see Overview doc, "Cron endpoint security").

    NOTE: if core/ already defines an equivalent shared helper (per the
    Overview's mention of a "cron authentication helper" in core), prefer
    that one instead and delete this file — this local copy exists so the
    trade app is self-contained even if core's helper has a different name.
    """
    provided = request.headers.get("X-CRON-SECRET")
    expected = getattr(settings, "CRON_SECRET_KEY", None)
    return bool(expected) and provided == expected