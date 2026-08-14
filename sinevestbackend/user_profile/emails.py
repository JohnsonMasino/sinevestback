from core.mailer import send_email


def send_profile_updated_email(user):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Profile Updated",
        template="user_profile/profile_updated.html",
        context={
            "first_name": user.first_name,
        },
    )