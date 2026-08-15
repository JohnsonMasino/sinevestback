from django.contrib import admin

from .models import Trade, TradePlan


@admin.register(TradePlan)
class TradePlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "min_amount", "max_amount", "profit_percentage", "duration_hours", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")

    def get_readonly_fields(self, request, obj=None):
        # code is the seeded primary key — read-only after creation, but
        # editable (in theory) when adding a brand-new plan row manually.
        if obj:
            return ("code",)
        return ()

    def has_add_permission(self, request):
        # Plans are seeded via data migration; discourage ad-hoc creation
        # from the admin, but don't hard-block it in case a 6th plan is
        # ever needed for a demo.
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan", "amount", "status", "started_at", "matures_at", "closed_at")
    list_filter = ("status", "plan")
    search_fields = ("user__email",)

    def get_readonly_fields(self, request, obj=None):
        # Everything stays locked EXCEPT the three timestamps. Trade closure
        # (status + actual_profit_paid) must only ever happen through the
        # cron endpoint, since that's the single code path that calls
        # wallet.services.unlock_and_credit() — letting status be edited
        # here would reproduce the exact bug we just fixed on withdrawals.
        editable_fields = ("started_at", "matures_at", "closed_at")
        return [f.name for f in Trade._meta.fields if f.name not in editable_fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False