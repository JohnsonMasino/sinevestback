from django.urls import path

from .views import (
    PinChangeConfirmView,
    PinChangeInitiateView,
    PinCreateView,
    TransactionPinDetailView,
)

app_name = "transaction_pin"

urlpatterns = [
    path("", TransactionPinDetailView.as_view(), name="transaction-pin-detail"),
    path("create/", PinCreateView.as_view(), name="transaction-pin-create"),
    path("change/initiate/", PinChangeInitiateView.as_view(), name="transaction-pin-change-initiate"),
    path("change/confirm/", PinChangeConfirmView.as_view(), name="transaction-pin-change-confirm"),
]