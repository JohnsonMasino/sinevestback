from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAccountActiveAndAllowedToAct

from .emails import send_profile_updated_email
from .models import Profile
from .serializers import ProfileSerializer


class ProfileView(APIView):
    """
    GET  /api/profile/  — combined User + Profile view, always accessible.
    PATCH /api/profile/ — update name and/or any profile/address fields.
                           Gated by IsAccountActiveAndAllowedToAct, since
                           profile update is a state-changing action per the
                           Overview's is_active rule; GET stays read-only
                           accessible regardless of account-active status.
    """

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [permissions.IsAuthenticated(), IsAccountActiveAndAllowedToAct()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        profile, _ = Profile.objects.select_related("user").get_or_create(user=self.request.user)
        return profile

    @extend_schema(responses={200: ProfileSerializer})
    def get(self, request):
        profile = self.get_object()
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    @extend_schema(request=ProfileSerializer, responses={200: ProfileSerializer})
    def patch(self, request):
        profile = self.get_object()
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        send_profile_updated_email(request.user)

        return Response(serializer.data)