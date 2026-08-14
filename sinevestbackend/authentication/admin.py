from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserChangeForm, UserCreationForm
from .models import OTP, PasswordResetToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "first_name", "last_name", "is_verified", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("is_verified", "is_active", "is_staff")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "updated_at")

    # No 'username' field on this model, so we fully redefine fieldsets
    # instead of relying on BaseUserAdmin's defaults.
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("date_joined", "updated_at")}),
        ("Identifiers", {"fields": ("id",)}),
    )

    # Fields shown on the 'Add user' page (uses add_form above)
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")


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