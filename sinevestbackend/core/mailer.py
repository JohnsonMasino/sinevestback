"""
core/mailer.py
──────────────
Single entry-point for all outbound email in NovafinAlliance.
Uses Mailgun's HTTP Messages API directly (no Django email backend / SMTP).

Usage
-----
from core.mailer import send_email

send_email(
    to       = 'user@example.com',
    subject  = 'Hello',
    template = 'authentication/otp_register.html',
    context  = {'otp_code': '123456', 'expiry_minutes': 10},
)
"""
import logging
import re

import requests
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email(
    to,
    subject: str,
    template: str,
    context: dict = None,
    from_email: str = None,
) -> bool:
    """
    Render an HTML email template and send it via Mailgun HTTP API.

    Parameters
    ----------
    to          : recipient email or list of emails
    subject     : email subject line
    template    : path to Django template  e.g. 'authentication/otp_register.html'
    context     : dict passed to the template renderer
    from_email  : override the default sender (uses DEFAULT_FROM_EMAIL if omitted)

    Returns
    -------
    True on success, False on failure (errors are logged, never raised).
    """
    if context is None:
        context = {}

    # Always inject the frontend URL so templates can build links
    context.setdefault('FRONTEND_URL', settings.FRONTEND_URL)

    # Render HTML body
    try:
        html_body = render_to_string(template, context)
    except Exception as exc:
        logger.error('mailer: template render failed (%s): %s', template, exc)
        return False

    # Build plain-text fallback by stripping tags (simple approach)
    text_body = re.sub(r'<[^>]+>', '', html_body)
    text_body = re.sub(r'\n{3,}', '\n\n', text_body).strip()

    # Normalise recipient list
    if isinstance(to, str):
        to = [to]

    sender = from_email or settings.DEFAULT_FROM_EMAIL

    payload = {
        'from': sender,
        'to': to,
        'subject': subject,
        'text': text_body,
        'html': html_body,
    }

    try:
        response = requests.post(
            f'https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages',
            auth=('api', settings.MAILGUN_API_KEY),
            data=payload,
            timeout=10,
        )
        if response.status_code == 200:
            logger.info('mailer: sent "%s" -> %s', subject, to)
            return True
        else:
            logger.error(
                'mailer: Mailgun returned %s for "%s" -> %s: %s',
                response.status_code, subject, to, response.text,
            )
            return False
    except requests.RequestException as exc:
        logger.error('mailer: request failed for "%s": %s', subject, exc)
        return False