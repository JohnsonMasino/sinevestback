from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    path("api/auth/", include("authentication.urls")),
    path("api/kyc/", include("kyc.urls")),
    path("api/wallet/", include("wallet.urls")),
    path("api/deposits/", include("deposit.urls")),
    path("api/cron/deposits/", include("deposit.urls_cron")),
    path("api/transaction-pin/", include("transaction_pin.urls")),
    path("api/withdrawals/", include("withdrawal.urls")),
]
