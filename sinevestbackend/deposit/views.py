from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct, IsCronRequest

from .emails import send_deposit_requested_email
from .models import Deposit
from .pagination import DepositPagination
from .serializers import DepositCreateSerializer, DepositSerializer


class DepositListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/deposits/ — list current user's deposit requests (paginated).
    POST /api/deposits/ — create a new deposit request.
    Admin approve/reject happens only in the Django admin, never here.
    """

    pagination_class = DepositPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAccountActiveAndAllowedToAct()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Deposit.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DepositCreateSerializer
        return DepositSerializer

    def perform_create(self, serializer):
        deposit = serializer.save(user=self.request.user)
        send_deposit_requested_email(self.request.user, deposit)
        self._created_instance = deposit

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Respond with the full read shape (id, status, created_at, processed_at, ...)
        # rather than just the {"amount"} the create serializer accepted.
        response.data = DepositSerializer(self._created_instance).data
        return response


class DepositDetailView(generics.RetrieveAPIView):
    """GET /api/deposits/{id}/ — retrieve a single deposit request."""

    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Deposit.objects.filter(user=self.request.user)


class ExpirePendingDepositsView(APIView):
    """
    POST /api/cron/deposits/expire-pending/
    Hit on a schedule by the external cron service (cronjob.org). Deletes any
    Deposit still 'pending' after PENDING_TRANSACTION_EXPIRY_MINUTES — a
    defensive cleanup for stale artifacts of a broken/interrupted frontend
    flow. Deposits are normally created in a single shot with no wallet
    effect while pending, so this mostly guards against future flow changes.
    """

    permission_classes = [IsCronRequest]

    def post(self, request):
        expiry_minutes = getattr(settings, "PENDING_TRANSACTION_EXPIRY_MINUTES", 5)
        cutoff = timezone.now() - timedelta(minutes=expiry_minutes)

        stale_qs = Deposit.objects.filter(status="pending", created_at__lt=cutoff)
        deleted_count = stale_qs.count()
        stale_qs.delete()

        return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)