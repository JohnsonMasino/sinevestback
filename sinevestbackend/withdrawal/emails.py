from core.mailer import send_email


def send_withdrawal_otp_email(user, withdrawal, otp_code):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Confirm Your Withdrawal",
        template="withdrawal/withdrawal_otp.html",
        context={
            "first_name": user.first_name,
            "amount": withdrawal.amount,
            "wallet_address": withdrawal.wallet_address,
            "otp_code": otp_code,
        },
    )


def send_withdrawal_submitted_email(user, withdrawal):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Withdrawal Submitted",
        template="withdrawal/withdrawal_submitted.html",
        context={
            "first_name": user.first_name,
            "amount": withdrawal.amount,
            "wallet_address": withdrawal.wallet_address,
            "withdrawal_id": withdrawal.id,
        },
    )


def send_withdrawal_completed_email(user, withdrawal):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Withdrawal Completed",
        template="withdrawal/withdrawal_completed.html",
        context={
            "first_name": user.first_name,
            "amount": withdrawal.amount,
            "wallet_address": withdrawal.wallet_address,
            "processed_at": withdrawal.processed_at,
        },
    )


def send_withdrawal_rejected_email(user, withdrawal):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Withdrawal Rejected",
        template="withdrawal/withdrawal_rejected.html",
        context={
            "first_name": user.first_name,
            "amount": withdrawal.amount,
            "wallet_address": withdrawal.wallet_address,
            "admin_notes": withdrawal.admin_notes,
        },
    )