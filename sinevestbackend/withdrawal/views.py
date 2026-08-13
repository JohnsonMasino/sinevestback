from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct

from .emails import (
    send_withdrawal_otp_email,
    send_withdrawal_submitted_email,
)
from .models import Withdrawal
from .serializers import (
    WithdrawalConfirmSerializer,
    WithdrawalInitiateSerializer,
    WithdrawalSerializer,
)
from .services import create_withdrawal_otp


class WithdrawalInitiateView(APIView):
    """POST /api/withdrawals/initiate/"""

    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndAllowedToAct]

    def post(self, request):
        serializer = WithdrawalInitiateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            withdrawal = serializer.save()
            otp = create_withdrawal_otp(withdrawal)

        send_withdrawal_otp_email(request.user, withdrawal, otp.code)

        return Response(
            {
                "id": str(withdrawal.id),
                "amount": str(withdrawal.amount),
                "wallet_address": withdrawal.wallet_address,
                "network": withdrawal.network,
                "status": withdrawal.status,
                "message": "An OTP has been sent to your email to confirm this withdrawal.",
            },
            status=status.HTTP_201_CREATED,
        )


class WithdrawalConfirmView(APIView):
    """POST /api/withdrawals/{id}/confirm/"""

    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndAllowedToAct]

    def post(self, request, pk):
        try:
            withdrawal = Withdrawal.objects.get(pk=pk, user=request.user)
        except Withdrawal.DoesNotExist:
            # Covers the case where the abandonment cron already deleted it.
            return Response(
                {"detail": "This withdrawal request has expired. Please start again."},
                status=status.HTTP_410_GONE,
            )

        if withdrawal.status != Withdrawal.Status.PENDING_OTP:
            return Response(
                {"detail": "This withdrawal request has already been confirmed or is no longer pending OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WithdrawalConfirmSerializer(
            data=request.data, context={"withdrawal": withdrawal}
        )
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data["otp"]

        with transaction.atomic():
            withdrawal = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            withdrawal.status = Withdrawal.Status.PENDING
            withdrawal.save(update_fields=["status"])

        send_withdrawal_submitted_email(request.user, withdrawal)

        return Response(
            {
                "id": str(withdrawal.id),
                "status": withdrawal.status,
                "message": "Withdrawal request submitted for processing.",
            },
            status=status.HTTP_200_OK,
        )


class WithdrawalListView(generics.ListAPIView):
    """GET /api/withdrawals/ — current user's withdrawal requests, paginated."""

    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user)


class WithdrawalDetailView(generics.RetrieveAPIView):
    """GET /api/withdrawals/{id}/"""

    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user)