from django.urls import path

from .views import (
    ActiveTradeListView,
    CleanupPendingTransactionsCronView,
    CloseExpiredTradesCronView,
    TradeCreateView,
    TradeDetailView,
    TradeHistoryListView,
    TradePlanListView,
)

app_name = "trade"

urlpatterns = [
    # Plan picker
    path("trade-plans/", TradePlanListView.as_view(), name="trade-plan-list"),
    # Trades
    path("trades/", TradeCreateView.as_view(), name="trade-create"),
    path("trades/active/", ActiveTradeListView.as_view(), name="trade-active-list"),
    path("trades/history/", TradeHistoryListView.as_view(), name="trade-history-list"),
    path("trades/<uuid:pk>/", TradeDetailView.as_view(), name="trade-detail"),
    # Cron
    path("cron/close-expired-trades/", CloseExpiredTradesCronView.as_view(), name="cron-close-expired-trades"),
    path(
        "cron/cleanup-pending-transactions/",
        CleanupPendingTransactionsCronView.as_view(),
        name="cron-cleanup-pending-transactions",
    ),
]