from django.contrib import admin

from .models import OTP, PasswordResetToken, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "is_verified", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_verified", "is_active", "is_staff")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "updated_at")


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Read-only in admin — for debugging only, never edited by hand."""

    list_display = ("user", "purpose", "code", "is_used", "expires_at", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("user__email", "code")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Read-only in admin — for debugging only, never edited by hand."""

    list_display = ("user", "is_used", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("user__email",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False