from django.urls import path

from .views import KYCCompletionView, KYCProfileView, KYCStatusView, KYCSubmitView

app_name = "kyc"

urlpatterns = [
    path("", KYCProfileView.as_view(), name="profile"),
    path("submit/", KYCSubmitView.as_view(), name="submit"),
    path("completion/", KYCCompletionView.as_view(), name="completion"),
    path("status/", KYCStatusView.as_view(), name="status"),
]