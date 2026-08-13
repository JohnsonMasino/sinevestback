"""
All outbound email for the authentication app. Every function here delegates
to the single shared sender in core/mailer.py — never call requests.post()
or Django's own email backend directly from this app.
"""

from core.mailer import send_email


def send_registration_otp_email(user, otp_code):
    return send_email(
        to=user.email,
        subject="Verify your Sinevest Premium account",
        template="authentication/otp_register.html",
        context={"user": user, "otp_code": otp_code},
    )


def send_password_reset_email(user, reset_link):
    return send_email(
        to=user.email,
        subject="Reset your Sinevest Premium password",
        template="authentication/password_reset.html",
        context={"user": user, "reset_link": reset_link},
    )


def send_password_changed_email(user):
    return send_email(
        to=user.email,
        subject="Your Sinevest Premium password was changed",
        template="authentication/password_changed.html",
        context={"user": user},
    )


def send_account_disabled_email(user):
    return send_email(
        to=user.email,
        subject="Your Sinevest Premium account has been disabled",
        template="authentication/account_disabled.html",
        context={"user": user},
    )