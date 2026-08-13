from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Wallet, WalletLedgerEntry
from .pagination import WalletLedgerPagination
from .serializers import WalletLedgerEntrySerializer, WalletSerializer


class WalletDetailView(RetrieveAPIView):
    """
    GET /api/wallet/ — current user's balance summary.
    No POST/PATCH here by design: balances only ever change as a side effect
    of an approved deposit, approved withdrawal, or a trade opening/closing,
    via wallet/services.py.
    """

    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet


class WalletLedgerListView(ListAPIView):
    """GET /api/wallet/ledger/ — paginated audit-trail entries for the current user."""

    serializer_class = WalletLedgerEntrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = WalletLedgerPagination

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return WalletLedgerEntry.objects.filter(wallet=wallet)