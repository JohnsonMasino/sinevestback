"""
core/responses.py
──────────────────
Shared response envelope helpers (overview doc §2).

Every endpoint — success or error, in every app — must return one of these
two shapes so the frontend never has to special-case a particular app:

    # success
    { "success": true,  "message": "...", "data": {...} }

    # error
    { "success": false, "message": "...", "errors": {...} }   # errors optional

Views should return these via DRF's Response, e.g.:

    from rest_framework import status
    from core.responses import success_response, error_response

    return success_response(
        message="Profile updated successfully.",
        data=serializer.data,
    )

    return error_response(
        message="Invalid transaction PIN.",
        errors={"transaction_pin": ["The PIN provided is incorrect."]},
        status_code=status.HTTP_400_BAD_REQUEST,
        code="INVALID_PIN",
    )
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(message: str = "Success", data=None, status_code: int = status.HTTP_200_OK):
    """
    Build a standard success envelope.

    `data` defaults to an empty dict (never omitted) so frontend code can
    always safely do `response.data.data` without an undefined check.
    """
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status_code,
    )


def error_response(
    message: str = "An error occurred",
    errors: dict = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    code: str = None,
):
    """
    Build a standard error envelope.

    `errors` is optional and, when present, follows DRF's field-error shape:
        {"field_name": ["specific error", ...]}

    `code` is an optional machine-readable identifier (e.g. "INVALID_PIN",
    "KYC_NOT_APPROVED", "PROFILE_INCOMPLETE") that the frontend can switch
    on without string-matching `message`. When provided it is placed at the
    top level of the envelope alongside `success`/`message`/`errors`.
    """
    body = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        body["errors"] = errors
    if code is not None:
        body["code"] = code

    return Response(body, status=status_code)