"""
core/exceptions.py
────────────────────
Custom DRF exception handler (overview doc §2).

Registered in settings.py as:
    REST_FRAMEWORK = {
        ...
        'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
    }

Guarantees that EVERY error response — DRF validation errors, permission
denials (403), not-found (404), throttling (429), auth failures (401), and
uncaught exceptions (500) — comes back in the shared envelope shape:

    { "success": false, "message": "...", "errors": {...} }

instead of DRF's raw default error format.
"""
import logging

from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def _flatten_first_message(detail) -> str:
    """
    Pull a single human-readable message out of DRF's (often nested)
    error detail structure, for use as the top-level `message` field.
    """
    if isinstance(detail, list) and detail:
        return _flatten_first_message(detail[0])
    if isinstance(detail, dict) and detail:
        first_value = next(iter(detail.values()))
        return _flatten_first_message(first_value)
    return str(detail)


def _as_errors_dict(detail):
    """
    Normalise DRF's error detail into the `errors: {field: [messages]}`
    shape. Non-field errors are bucketed under "non_field_errors".
    """
    if isinstance(detail, dict):
        errors = {}
        for field, value in detail.items():
            errors[field] = value if isinstance(value, list) else [value]
        return errors
    if isinstance(detail, list):
        return {"non_field_errors": [str(item) for item in detail]}
    return {"non_field_errors": [str(detail)]}


def custom_exception_handler(exc, context):
    """
    Wrap every exception DRF knows how to handle (and a few Django ones)
    into the shared { success, message, errors } envelope.
    """
    # Translate a couple of plain Django exceptions into DRF ones first,
    # so they flow through the same formatting logic below.
    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = drf_exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)

    if response is not None:
        message = _flatten_first_message(response.data)
        errors = _as_errors_dict(response.data)

        envelope = {
            "success": False,
            "message": message,
            "errors": errors,
        }

        # Preserve machine-readable codes set by custom permission classes
        # (core.permissions) such as PROFILE_INCOMPLETE / KYC_NOT_APPROVED /
        # INVALID_PIN, so the frontend can branch on `code` instead of
        # parsing `message` strings.
        code = getattr(exc, "default_code_override", None) or getattr(exc, "code", None)
        if code and isinstance(code, str) and code.isupper():
            envelope["code"] = code

        response.data = envelope
        return response

    # DRF didn't recognise the exception at all (i.e. it would otherwise
    # bubble up as a raw Django 500). Log it and return a safe envelope
    # instead of leaking a stack trace to the client.
    logger.exception("Unhandled exception in view: %s", exc)
    return Response(
        {
            "success": False,
            "message": "Something went wrong on our end. Please try again shortly.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )