from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class _CodedPermissionDenied(PermissionDenied):
    """
    PermissionDenied subclass that also carries a machine-readable `code`,
    picked up by core.exceptions.custom_exception_handler and surfaced as
    the envelope's top-level `code` field (e.g. "PROFILE_INCOMPLETE").
    """
    def __init__(self, detail, code):
        super().__init__(detail=detail)
        self.default_code_override = code


class IsActiveUser(BasePermission):
    """
    Blocks any request from a user an admin has deactivated
    (request.user.is_active == False) via Django Admin.
    """
    message = "Your account has an issue. Please contact an administrator to resolve your case."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return True  # let IsAuthenticated handle unauthenticated requests
        if not user.is_active:
            raise _CodedPermissionDenied(detail=self.message, code="ACCOUNT_INACTIVE")
        return True


class IsProfileComplete(BasePermission):
    """
    Blocks access until the user has finished their profile.
    Surfaces machine-readable code PROFILE_INCOMPLETE so the frontend can
    trigger the "complete your profile" popup instead of showing a generic error.
    """
    message = "Please complete your profile to continue."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return True
        if not getattr(user, "profile_completed", False):
            raise _CodedPermissionDenied(detail=self.message, code="PROFILE_INCOMPLETE")
        return True


class IsKYCApproved(BasePermission):
    """
    Blocks transfers, loans, cards, and wallet account generation until
    KYC has been approved by an admin.
    Surfaces machine-readable code KYC_NOT_APPROVED.
    """
    message = "Please complete and wait for approval of your KYC to continue."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return True
        if getattr(user, "kyc_status", None) != "approved":
            raise _CodedPermissionDenied(detail=self.message, code="KYC_NOT_APPROVED")
        return True

class IsAccountActiveAndAllowedToAct(BasePermission):
    """
    Allows authenticated users to perform account actions only when
    their Django account is active.

    Used by KYC and other account-action endpoints.
    """

    message = (
        "Your account is not currently allowed to perform this action. "
        "Please contact an administrator."
    )

    def has_permission(self, request, view):
        user = request.user

        # Let IsAuthenticated handle unauthenticated users.
        if not user or not user.is_authenticated:
            return True

        if not user.is_active:
            raise _CodedPermissionDenied(
                detail=self.message,
                code="ACCOUNT_INACTIVE",
            )

        return True

class IsCronRequest(BasePermission):
    """
    Allows access only to requests containing the configured cron secret.

    Expected header:

        X-Cron-Secret: <CRON_SECRET>

    The secret must be stored in the environment and exposed through
    Django settings.
    """

    message = "Invalid or missing cron authentication."

    def has_permission(self, request, view):
        configured_secret = getattr(settings, "CRON_SECRET", "")

        if not configured_secret:
            raise _CodedPermissionDenied(
                detail="Cron authentication is not configured.",
                code="CRON_NOT_CONFIGURED",
            )

        provided_secret = request.headers.get("X-Cron-Secret", "")

        if not provided_secret:
            raise _CodedPermissionDenied(
                detail=self.message,
                code="CRON_AUTH_REQUIRED",
            )

        if provided_secret != configured_secret:
            raise _CodedPermissionDenied(
                detail=self.message,
                code="CRON_AUTH_INVALID",
            )

        return True