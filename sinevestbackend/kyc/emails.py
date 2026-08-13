"""
All outbound email for the kyc app. Every function delegates to the single
shared sender in core/mailer.py — never call requests.post() or Django's
own email backend directly from this app.
"""

from core.mailer import send_email


def send_kyc_submission_received_email(user):
    return send_email(
        to=user.email,
        subject="We've received your Sinevest Premium KYC submission",
        template="kyc/kyc_submitted.html",
        context={"user": user},
    )


def send_kyc_approved_email(user):
    return send_email(
        to=user.email,
        subject="Your Sinevest Premium KYC has been approved",
        template="kyc/kyc_approved.html",
        context={"user": user},
    )


def send_kyc_rejected_email(user, reason=""):
    return send_email(
        to=user.email,
        subject="Update on your Sinevest Premium KYC submission",
        template="kyc/kyc_rejected.html",
        context={"user": user, "reason": reason},
    )


def send_kyc_admin_notification_email(user):
    """
    Optional internal notification sent to settings.ADMIN_NOTIFICATION_EMAIL
    whenever a user submits KYC for review. Only fired if that setting is
    configured — see kyc/views.py::KYCSubmitView.
    """
    from django.conf import settings

    admin_email = getattr(settings, "ADMIN_NOTIFICATION_EMAIL", "")
    if not admin_email:
        return False

    return send_email(
        to=admin_email,
        subject="New KYC submission pending review",
        template="kyc/kyc_admin_notification.html",
        context={"user": user},
    )