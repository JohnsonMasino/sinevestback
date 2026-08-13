from core.mailer import send_email


def send_pin_created_email(user):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Transaction PIN Created",
        template="transaction_pin/pin_created.html",
        context={
            "first_name": user.first_name,
        },
    )


def send_pin_change_otp_email(user, otp_code):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Confirm Your PIN Change",
        template="transaction_pin/pin_change_otp.html",
        context={
            "first_name": user.first_name,
            "otp_code": otp_code,
        },
    )


def send_pin_changed_email(user):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Transaction PIN Changed",
        template="transaction_pin/pin_changed.html",
        context={
            "first_name": user.first_name,
        },
    )