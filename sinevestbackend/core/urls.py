from django.urls import path, include
from django.contrib import admin
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path("api/auth/", include("authentication.urls")),
    path("api/kyc/", include("kyc.urls")),
    path("api/wallet/", include("wallet.urls")),
    path("api/deposits/", include("deposit.urls")),
    path("api/cron/deposits/", include("deposit.urls_cron")),
    path("api/transaction-pin/", include("transaction_pin.urls")),
    path("api/withdrawals/", include("withdrawal.urls")),
    path("api/", include("trade.urls")),                    # fixed
    path("api/", include("transaction_history.urls")),      # fixed
    path("api/user-profile/", include("user_profile.urls")),

    # Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]