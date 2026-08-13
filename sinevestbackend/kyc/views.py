from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct

from .emails import send_kyc_admin_notification_email, send_kyc_submission_received_email
from .models import KYCProfile
from .serializers import (
    KYCCompletionSerializer,
    KYCProfileReadSerializer,
    KYCProfileUpdateSerializer,
    KYCStatusSerializer,
    KYCSubmitResponseSerializer,
)
from .utils import compute_kyc_completion


class KYCProfileView(APIView):
    """
    GET  /api/kyc/  — full profile, nested by section.
    PATCH /api/kyc/ — partial update, one or more sections/fields at once.
    """

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsAccountActiveAndAllowedToAct()]
        return [IsAuthenticated()]

    def get_object(self, user):

        profile, _ = KYCProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self.get_object(request.user)
        return Response(KYCProfileReadSerializer(profile).data, status=status.HTTP_200_OK)

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
                **KYCSubmitResponseSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )


class KYCCompletionView(APIView):
    """GET /api/kyc/completion/ — overall + per-section completion percentage."""

    permission_classes = [IsAuthenticated]

    def get(self, request):

        profile, _ = KYCProfile.objects.get_or_create(user=request.user)
        overall, sections = compute_kyc_completion(profile)

        data = {"overall_percentage": overall, "sections": sections}
        return Response(KYCCompletionSerializer(data).data, status=status.HTTP_200_OK)


class KYCStatusView(APIView):
    """GET /api/kyc/status/ — lightweight status-only endpoint."""

    permission_classes = [IsAuthenticated]

    def get(self, request):

        profile, _ = KYCProfile.objects.get_or_create(user=request.user)
        return Response(KYCStatusSerializer(profile).data, status=status.HTTP_200_OK)