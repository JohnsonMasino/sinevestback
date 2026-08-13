from django.urls import path

from .views import WalletDetailView, WalletLedgerListView

app_name = "wallet"

urlpatterns = [
    path("", WalletDetailView.as_view(), name="detail"),
    path("ledger/", WalletLedgerListView.as_view(), name="ledger"),
]