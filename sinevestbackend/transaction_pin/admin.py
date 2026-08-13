from django.contrib import admin

from .models import PinChangeOTP, TransactionPin


@admin.register(TransactionPin)
class TransactionPinAdmin(admin.ModelAdmin):
    list_display = ("user", "is_set", "updated_at")
    search_fields = ("user__email",)
    list_filter = ("is_set",)
    readonly_fields = ("id", "created_at", "updated_at")
    # pin_hash is intentionally excluded from the admin form entirely —
    # it must never be surfaced, even hashed.
    exclude = ("pin_hash",)

    def has_add_permission(self, request):
        return False


@admin.register(PinChangeOTP)
class PinChangeOTPAdmin(admin.ModelAdmin):
    """Read-only, for debugging only."""

    list_display = ("user", "code", "is_used", "expires_at", "created_at")
    search_fields = ("user__email", "code")
    list_filter = ("is_used",)
    readonly_fields = [f.name for f in PinChangeOTP._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True