from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils.dateparse import parse_date

from .pagination import TransactionPagination
from .serializers import TransactionSummarySerializer, UnifiedTransactionSerializer
from .services import get_summary, get_unified_transactions

_COMMON_PARAMS = [
    OpenApiParameter("status", str, description="Filter by status, e.g. 'completed'."),
    OpenApiParameter("date_from", str, description="ISO date, e.g. '2026-08-01'. Filters created_at >=."),
    OpenApiParameter("date_to", str, description="ISO date, e.g. '2026-08-13'. Filters created_at <=."),
    OpenApiParameter("page", int, description="Page number."),
    OpenApiParameter("page_size", int, description="Results per page (max 100)."),
]


class _BaseTransactionListView(APIView):
    """
    Shared GET handler. Subclasses set `fixed_type` to lock the endpoint to
    one source (deposit/withdrawal/trade), or leave it None for the combined
    endpoint where `?type=` becomes a query filter instead.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = TransactionPagination
    fixed_type: str | None = None

    def get(self, request):
        type_filter = self.fixed_type or request.query_params.get("type")

        status_filter = request.query_params.get("status")

        raw_date_from = request.query_params.get("date_from")
        raw_date_to = request.query_params.get("date_to")
        date_from = parse_date(raw_date_from) if raw_date_from else None
        date_to = parse_date(raw_date_to) if raw_date_to else None

        entries = get_unified_transactions(
            request.user,
            type_filter=type_filter,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(entries, request, view=self)
        return paginator.get_paginated_response(page)


@extend_schema(
    parameters=[OpenApiParameter("type", str, description="Filter to one type: deposit, withdrawal, trade.")]
    + _COMMON_PARAMS,
    responses=UnifiedTransactionSerializer(many=True),
)
class CombinedTransactionListView(_BaseTransactionListView):
    """GET /api/transactions/ — merged history across all three sources."""

    fixed_type = None


@extend_schema(parameters=_COMMON_PARAMS, responses=UnifiedTransactionSerializer(many=True))
class DepositTransactionListView(_BaseTransactionListView):
    """GET /api/transactions/deposits/"""

    fixed_type = "deposit"


@extend_schema(parameters=_COMMON_PARAMS, responses=UnifiedTransactionSerializer(many=True))
class WithdrawalTransactionListView(_BaseTransactionListView):
    """GET /api/transactions/withdrawals/ — excludes pending_otp rows."""

    fixed_type = "withdrawal"


@extend_schema(parameters=_COMMON_PARAMS, responses=UnifiedTransactionSerializer(many=True))
class TradeTransactionListView(_BaseTransactionListView):
    """GET /api/transactions/trades/"""

    fixed_type = "trade"


class TransactionSummaryView(APIView):
    """GET /api/transactions/summary/ — lightweight counts/totals per type."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=TransactionSummarySerializer)
    def get(self, request):
        return Response(get_summary(request.user))