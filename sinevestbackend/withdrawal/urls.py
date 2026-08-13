from django.urls import path

from .views import (
    WithdrawalConfirmView,
    WithdrawalDetailView,
    WithdrawalInitiateView,
    WithdrawalListView,
)

app_name = "withdrawal"

urlpatterns = [
    path("", WithdrawalListView.as_view(), name="withdrawal-list"),
    path("initiate/", WithdrawalInitiateView.as_view(), name="withdrawal-initiate"),
    path("<uuid:pk>/confirm/", WithdrawalConfirmView.as_view(), name="withdrawal-confirm"),
    path("<uuid:pk>/", WithdrawalDetailView.as_view(), name="withdrawal-detail"),
]