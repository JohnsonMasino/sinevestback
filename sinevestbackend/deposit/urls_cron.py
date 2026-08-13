from django.urls import path

from .views import ExpirePendingDepositsView

app_name = "deposit-cron"

urlpatterns = [
    path("expire-pending/", ExpirePendingDepositsView.as_view(), name="expire-pending"),
]