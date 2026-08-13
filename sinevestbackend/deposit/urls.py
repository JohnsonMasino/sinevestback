from django.urls import path

from .views import DepositDetailView, DepositListCreateView

app_name = "deposit"

urlpatterns = [
    path("", DepositListCreateView.as_view(), name="list-create"),
    path("<uuid:pk>/", DepositDetailView.as_view(), name="detail"),
]