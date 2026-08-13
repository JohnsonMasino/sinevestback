"""
core/health.py
────────────────
GET /health/ — no auth required (overview doc §7).

Point UptimeRobot (or any pinger) at this every 10 minutes to keep the
Render free-tier instance from idling. This intentionally does NOT touch
the database or any other dependency — it should stay fast and always-up
even if something downstream is degraded.
"""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health_check(request):
    return Response(
        {
            "status": "ok",
            "timestamp": timezone.now().isoformat(),
        }
    )