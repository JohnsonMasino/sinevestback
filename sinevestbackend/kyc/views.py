from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct

from .emails import send_kyc_admin_notification_email, send_kyc_submission_received_email
from .models import KYCProfile
from .serializers import (
    ErrorDetailSerializer,
    KYCCompletionSerializer,
    KYCProfileReadSerializer,
    KYCProfileUpdateSerializer,
    KYCStatusSerializer,
    KYCSubmitFullResponseSerializer,
)
from .utils import compute_kyc_completion


class KYCProfileView(APIView):
    """
    GET  /api/kyc/  — full profile, nested by section.
    PATCH /api/kyc/ — partial update, one or more sections/fields at once.

    A KYCProfile row is auto-created on first access if one doesn't exist
    yet (starts entirely blank, status="not_submitted"), so this endpoint
    never 404s for an authenticated user.
    """

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsAccountActiveAndAllowedToAct()]
        return [IsAuthenticated()]

    def get_object(self, user):

        profile, _ = KYCProfile.objects.get_or_create(user=user)
        return profile

    @extend_schema(
        summary="Get current user's KYC profile",
        description=(
            "Returns the full KYC profile, grouped into sections: personal_and_address, "
            "employment, government_id, trading_expertise, compliance — plus the top-level "
            "status, submitted_at, reviewed_at, and admin_notes fields. Fields not yet filled "
            "in come back as null/blank. Auto-creates a blank profile on first call."
        ),
        responses={200: KYCProfileReadSerializer},
    )
    def get(self, request):
        profile = self.get_object(request.user)
        return Response(KYCProfileReadSerializer(profile).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update KYC profile fields",
        description=(
            "Accepts any subset of the flat KYC fields (personal, address, employment, "
            "government ID, trading expertise, compliance) in a single PATCH — field names "
            "match the model directly, e.g. {\"country\": \"Nigeria\", \"occupation\": \"Engineer\"}. "
            "Only allowed while status is 'not_submitted' or 'rejected' — once a submission is "
            "'pending' or 'approved', the profile is locked and this returns 403 until an admin "
            "resets it."
        ),
        request=KYCProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(
                response=KYCProfileReadSerializer,
                description="Updated successfully. Returns the full profile in the same nested shape as GET.",
            ),
            400: OpenApiResponse(
                description="Validation error — field name(s) map to a list of error messages, e.g. "
                "an invalid choice value for a CharField with `choices`.",
                examples=[
                    OpenApiExample(
                        "Invalid choice",
                        value={"gender": ['"invalid" is not a valid choice.']},
                    )
                ],
            ),
            403: OpenApiResponse(
                response=ErrorDetailSerializer,
                description="Profile is locked because status is 'pending' or 'approved'.",
                examples=[
                    OpenApiExample(
                        "Locked",
                        value={
                            "detail": "KYC data cannot be edited while status is 'pending'. "
                            "An admin must reset it before further changes."
                        },
                    )
                ],
            ),
        },
    )
    def patch(self, request):
        profile = self.get_object(request.user)

        if not profile.is_editable:
            return Response(
                {
                    "detail": (
                        f"KYC data cannot be edited while status is '{profile.status}'. "
                        "An admin must reset it before further changes."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = KYCProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(KYCProfileReadSerializer(profile).data, status=status.HTTP_200_OK)


class KYCSubmitView(APIView):
    """POST /api/kyc/submit/ — move status to pending for admin review."""

    permission_classes = [IsAuthenticated, IsAccountActiveAndAllowedToAct]

    @extend_schema(
        summary="Submit KYC for review",
        description=(
            "Moves the profile from 'not_submitted'/'rejected' to 'pending', stamps "
            "submitted_at, and emails both the user (confirmation) and the admin notification "
            "address (if configured). Requires agreed_to_terms to already be true — set it via "
            "PATCH /api/kyc/ first if needed. Takes no request body; submits whatever data is "
            "already saved on the profile."
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                response=KYCSubmitFullResponseSerializer,
                description="Submitted successfully.",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "message": "KYC submitted for review.",
                            "status": "pending",
                            "submitted_at": "2026-08-13T09:00:00Z",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(
                description="Either already submitted, or terms not yet agreed to.",
                examples=[
                    OpenApiExample(
                        "Already pending/approved",
                        value={"detail": "KYC is already 'pending' and cannot be resubmitted."},
                    ),
                    OpenApiExample(
                        "Terms not agreed",
                        value={"agreed_to_terms": ["You must agree to the terms before submitting."]},
                    ),
                ],
            ),
        },
    )
    def post(self, request):

        profile, _ = KYCProfile.objects.get_or_create(user=request.user)

        if not profile.is_editable:
            return Response(
                {"detail": f"KYC is already '{profile.status}' and cannot be resubmitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not profile.agreed_to_terms:
            return Response(
                {"agreed_to_terms": ["You must agree to the terms before submitting."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.status = "pending"
        profile.submitted_at = timezone.now()
        profile.save(update_fields=["status", "submitted_at"])

        send_kyc_submission_received_email(request.user)
        if getattr(settings, "ADMIN_NOTIFICATION_EMAIL", ""):
            send_kyc_admin_notification_email(request.user)

        return Response(
            {
                "message": "KYC submitted for review.",
                "status": profile.status,
                "submitted_at": profile.submitted_at,
            },
            status=status.HTTP_200_OK,
        )


class KYCCompletionView(APIView):
    """GET /api/kyc/completion/ — overall + per-section completion percentage."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get KYC completion percentage",
        description=(
            "Returns an overall completion percentage (0-100) plus a per-section breakdown, "
            "useful for a frontend progress bar / checklist. Computed live from which fields "
            "are currently filled in — nothing here is stored."
        ),
        responses={
            200: OpenApiResponse(
                response=KYCCompletionSerializer,
                examples=[
                    OpenApiExample(
                        "Partially complete",
                        value={
                            "overall_percentage": 62,
                            "sections": {
                                "personal_and_address": 100,
                                "employment": 80,
                                "government_id": 25,
                                "trading_expertise": 100,
                                "compliance": 50,
                            },
                        },
                    )
                ],
            )
        },
    )
    def get(self, request):

        profile, _ = KYCProfile.objects.get_or_create(user=request.user)
        overall, sections = compute_kyc_completion(profile)

        data = {"overall_percentage": overall, "sections": sections}
        return Response(KYCCompletionSerializer(data).data, status=status.HTTP_200_OK)


class KYCStatusView(APIView):
    """GET /api/kyc/status/ — lightweight status-only endpoint."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get KYC status",
        description=(
            "Lightweight endpoint returning just status/submitted_at/reviewed_at — useful when "
            "the frontend only needs to check approval state (e.g. to gate a feature) without "
            "pulling the full nested profile."
        ),
        responses={
            200: OpenApiResponse(
                response=KYCStatusSerializer,
                examples=[
                    OpenApiExample(
                        "Approved",
                        value={
                            "status": "approved",
                            "submitted_at": "2026-08-10T09:00:00Z",
                            "reviewed_at": "2026-08-11T14:30:00Z",
                        },
                    ),
                    OpenApiExample(
                        "Not submitted yet",
                        value={"status": "not_submitted", "submitted_at": None, "reviewed_at": None},
                    ),
                ],
            )
        },
    )
    def get(self, request):

        profile, _ = KYCProfile.objects.get_or_create(user=request.user)
        return Response(KYCStatusSerializer(profile).data, status=status.HTTP_200_OK)