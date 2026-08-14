from django.urls import path

from .views import (
    CombinedTransactionListView,
    DepositTransactionListView,
    TradeTransactionListView,
    TransactionSummaryView,
    WithdrawalTransactionListView,
)

app_name = "transaction_history"

urlpatterns = [
    path("transactions/", CombinedTransactionListView.as_view(), name="transaction-combined-list"),
    path("transactions/deposits/", DepositTransactionListView.as_view(), name="transaction-deposits-list"),
    path("transactions/withdrawals/", WithdrawalTransactionListView.as_view(), name="transaction-withdrawals-list"),
    path("transactions/trades/", TradeTransactionListView.as_view(), name="transaction-trades-list"),
    path("transactions/summary/", TransactionSummaryView.as_view(), name="transaction-summary"),
]