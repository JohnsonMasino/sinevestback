import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct

from .emails import send_trade_activated_email, send_trade_expired_email
from .models import Trade, TradePlan
from .permissions import is_valid_cron_secret
from .serializers import (
    ActiveTradeSerializer,
    CronCleanupResponseSerializer,
    CronCloseExpiredTradesResponseSerializer,
    TradeCreateResponseSerializer,
    TradeCreateSerializer,
    TradeDetailSerializer,
    TradeHistorySerializer,
    TradePlanSerializer,
)

logger = logging.getLogger(__name__)


class TradePlanListView(generics.ListAPIView):
    """GET /api/trade-plans/ — public or token; lists the five active plans."""

    serializer_class = TradePlanSerializer
    permission_classes = [AllowAny]
    queryset = TradePlan.objects.filter(is_active=True)


class TradeCreateView(APIView):
    """POST /api/trades/ — open a new trade against a chosen plan."""

    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndAllowedToAct]

    @extend_schema(request=TradeCreateSerializer, responses={201: TradeCreateResponseSerializer})
    def post(self, request):
        serializer = TradeCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        trade = serializer.save()

        send_trade_activated_email(request.user, trade)

        response_serializer = TradeCreateResponseSerializer(trade)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ActiveTradeListView(generics.ListAPIView):
    """GET /api/trades/active/ — current user's active trades with live countdown."""

    serializer_class = ActiveTradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # doc shows a plain list, not paginated

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user, status=Trade.Status.ACTIVE).select_related("plan")


class TradeHistoryListView(generics.ListAPIView):
    """GET /api/trades/history/ — all of the current user's trades, any status, paginated."""

    serializer_class = TradeHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user).select_related("plan")


class TradeDetailView(generics.RetrieveAPIView):
    """GET /api/trades/{id}/"""

    serializer_class = TradeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user).select_related("plan")


class CloseExpiredTradesCronView(APIView):
    """
    POST /api/cron/close-expired-trades/
    Header: X-CRON-SECRET

    Closes every active trade whose matures_at has passed, crediting
    principal + profit back to the wallet. Each trade's closure is wrapped
    in its own transaction so one failure doesn't block the rest of the run.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={
            200: CronCloseExpiredTradesResponseSerializer,
            401: OpenApiResponse(description="Missing or invalid X-CRON-SECRET header."),
        },
    )
    def post(self, request):
        if not is_valid_cron_secret(request):
            return Response({"detail": "Invalid cron secret."}, status=status.HTTP_401_UNAUTHORIZED)

        from wallet.services import unlock_and_credit

        now = timezone.now()
        matured_trade_ids = list(
            Trade.objects.filter(status=Trade.Status.ACTIVE, matures_at__lte=now).values_list("id", flat=True)
        )

        closed_ids = []
        for trade_id in matured_trade_ids:
            try:
                with transaction.atomic():
                    # of=("self",) restricts the FOR UPDATE lock to the
                    # Trade row itself. Without it, Postgres tries to lock
                    # across the select_related("user__wallet") join too —
                    # and since that's a reverse one-to-one, Django can only
                    # build it as a LEFT OUTER JOIN, which Postgres refuses
                    # to lock ("FOR UPDATE cannot be applied to the nullable
                    # side of an outer join"). select_related is still kept
                    # here so plan/wallet are eager-loaded; only the lock
                    # itself is scoped down.
                    trade = (
                        Trade.objects.select_for_update(of=("self",))
                        .select_related("plan", "user__wallet")
                        .get(id=trade_id, status=Trade.Status.ACTIVE)
                    )
                    trade.actual_profit_paid = trade.expected_profit
                    unlock_and_credit(
                        trade.user.wallet,
                        principal=trade.amount,
                        profit=trade.actual_profit_paid,
                        reason=f"Trade #{trade.id} payout",
                    )
                    trade.status = Trade.Status.COMPLETED
                    trade.closed_at = timezone.now()
                    trade.save(update_fields=["status", "closed_at", "actual_profit_paid"])

                send_trade_expired_email(trade.user, trade)
                closed_ids.append(str(trade_id))
            except Exception:
                logger.exception("Failed to close trade %s during cron run", trade_id)
                continue

        return Response(
            {"trades_closed": len(closed_ids), "trade_ids": closed_ids},
            status=status.HTTP_200_OK,
        )


class CleanupPendingTransactionsCronView(APIView):
    """
    POST /api/cron/cleanup-pending-transactions/
    Header: X-CRON-SECRET

    Shared cleanup job referenced by the withdrawal app doc: deletes
    abandoned pending_otp Withdrawal rows, and (for forward-compatibility)
    would delete stale pending Deposit rows if/when the deposit app adopts
    a multi-step flow. See INTEGRATION_NOTES.md for the deposit-side wiring.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={
            200: CronCleanupResponseSerializer,
            401: OpenApiResponse(description="Missing or invalid X-CRON-SECRET header."),
        },
    )
    def post(self, request):
        if not is_valid_cron_secret(request):
            return Response({"detail": "Invalid cron secret."}, status=status.HTTP_401_UNAUTHORIZED)

        from withdrawal.services import cleanup_abandoned_withdrawals

        withdrawals_deleted = cleanup_abandoned_withdrawals()

        deposits_deleted = 0
        try:
            from deposit.services import cleanup_abandoned_deposits  # type: ignore

            deposits_deleted = cleanup_abandoned_deposits()
        except ImportError:
            # Deposits are currently single-step (no pending intermediate
            # state), so this is a no-op today. See INTEGRATION_NOTES.md.
            pass

        return Response(
            {"withdrawals_deleted": withdrawals_deleted, "deposits_deleted": deposits_deleted},
            status=status.HTTP_200_OK,
        )