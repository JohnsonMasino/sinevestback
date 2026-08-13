"""
All outbound email for the deposit app. Every function delegates to the
single shared sender in core/mailer.py — never call requests.post() or
Django's own email backend directly from this app.
"""

from core.mailer import send_email


def send_deposit_requested_email(user, deposit):
    return send_email(
        to=user.email,
        subject="We've received your Sinevest Premium deposit request",
        template="deposit/deposit_requested.html",
        context={"user": user, "deposit": deposit},
    )


def send_deposit_approved_email(user, deposit):
    return send_email(
        to=user.email,
        subject="Your Sinevest Premium deposit has been approved",
        template="deposit/deposit_approved.html",
        context={"user": user, "deposit": deposit},
    )


def send_deposit_rejected_email(user, deposit):
    return send_email(
        to=user.email,
        subject="Update on your Sinevest Premium deposit request",
        template="deposit/deposit_rejected.html",
        context={"user": user, "deposit": deposit},
    )