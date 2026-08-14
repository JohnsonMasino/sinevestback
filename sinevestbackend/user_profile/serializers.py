from django.db import transaction
from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.Serializer):
    """
    Not a ModelSerializer, since the response combines two models (User +
    Profile) into one flat shape. `instance` passed in is always a Profile
    object; user-owned fields (email, first_name, last_name) are read from
    / written to instance.user.
    """

    # From User — email is read-only (email changes are out of scope here;
    # they belong to a future verified-email-change flow in authentication).
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    # Personal
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(choices=Profile.Gender.choices, required=False, allow_null=True)
    bio = serializers.CharField(max_length=255, required=False, allow_blank=True)

    # Address
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    street_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)

    # System
    updated_at = serializers.DateTimeField(read_only=True)

    _PROFILE_FIELDS = (
        "phone_number",
        "date_of_birth",
        "gender",
        "bio",
        "country",
        "state",
        "city",
        "street_address",
        "postal_code",
    )

    def to_representation(self, instance: Profile):
        user = instance.user
        data = {
            "email": self.fields["email"].to_representation(user.email),
            "first_name": self.fields["first_name"].to_representation(user.first_name),
            "last_name": self.fields["last_name"].to_representation(user.last_name),
        }
        for name in self._PROFILE_FIELDS:
            value = getattr(instance, name)
            data[name] = self.fields[name].to_representation(value) if value is not None else None
        data["updated_at"] = self.fields["updated_at"].to_representation(instance.updated_at)
        return data

    def update(self, instance: Profile, validated_data):
        user = instance.user

        user_updates = {}
        for field_name in ("first_name", "last_name"):
            if field_name in validated_data:
                user_updates[field_name] = validated_data.pop(field_name)

        with transaction.atomic():
            if user_updates:
                for field_name, value in user_updates.items():
                    setattr(user, field_name, value)
                user.save(update_fields=list(user_updates.keys()))

            for field_name in self._PROFILE_FIELDS:
                if field_name in validated_data:
                    setattr(instance, field_name, validated_data[field_name])
            instance.save()

        return instance