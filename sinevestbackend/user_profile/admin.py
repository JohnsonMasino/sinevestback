from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Fully editable by staff for support purposes — unlike wallet/trade,
    there's no audit-integrity reason to lock this down; it's contact and
    address info, not financial history.
    """

    list_display = ("user", "phone_number", "country", "city", "updated_at")
    search_fields = ("user__email", "phone_number")
    list_filter = ("country",)
    readonly_fields = ("updated_at",)