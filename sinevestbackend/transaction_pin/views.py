from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct

from .emails import (
    send_pin_change_otp_email,
    send_pin_changed_email,
    send_pin_created_email,
)
from .models import TransactionPin
from .serializers import (
    MessageResponseSerializer,
    PinChangeConfirmSerializer,
    PinChangeInitiateSerializer,
    PinCreateSerializer,
    TransactionPinDetailSerializer,
)


class TransactionPinDetailView(generics.RetrieveAPIView):
    """GET /api/transaction-pin/ — read-only, is_set + timestamps only."""

    serializer_class = TransactionPinDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        tp, _ = TransactionPin.objects.get_or_create(user=self.request.user)
        return tp


class PinCreateView(APIView):
    """POST /api/transaction-pin/create/ — first-time PIN setup, no OTP required."""

    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndAllowedToAct]

    @extend_schema(request=PinCreateSerializer, responses={201: MessageResponseSerializer})
    def post(self, request):
        serializer = PinCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        send_pin_created_email(request.user)

        return Response(
            {"message": "Transaction PIN created successfully."},
            status=status.HTTP_201_CREATED,
        )


class PinChangeInitiateView(APIView):
    """POST /api/transaction-pin/change/initiate/ — verifies current PIN, sends OTP."""

    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndAllowedToAct]

    @extend_schema(request=PinChangeInitiateSerializer, responses={200: MessageResponseSerializer})
    def post(self, request):
        serializer = PinChangeInitiateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        otp = serializer.save()

        send_pin_change_otp_email(request.user, otp.code)

        return Response(
            {"message": "An OTP has been sent to your email to confirm this change."},
            status=status.HTTP_200_OK,
        )


class PinChangeConfirmView(APIView):
    """POST /api/transaction-pin/change/confirm/ — verifies OTP, finalizes new PIN."""

    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndAllowedToAct]

    @extend_schema(request=PinChangeConfirmSerializer, responses={200: MessageResponseSerializer})
    def post(self, request):
        serializer = PinChangeConfirmSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        send_pin_changed_email(request.user)

        return Response(
            {"message": "Transaction PIN changed successfully."},
            status=status.HTTP_200_OK,
        )