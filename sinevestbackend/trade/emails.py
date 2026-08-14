from core.mailer import send_email


def send_trade_activated_email(user, trade):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Trade Activated",
        template="trade/trade_activated.html",
        context={
            "first_name": user.first_name,
            "plan_name": trade.plan.name,
            "amount": trade.amount,
            "expected_profit": trade.expected_profit,
            "matures_at": trade.matures_at,
        },
    )


def send_trade_expired_email(user, trade):
    return send_email(
        to=user.email,
        subject="Sinevest Premium — Trade Completed",
        template="trade/trade_expired.html",
        context={
            "first_name": user.first_name,
            "plan_name": trade.plan.name,
            "amount": trade.amount,
            "actual_profit_paid": trade.actual_profit_paid,
            "closed_at": trade.closed_at,
        },
    )