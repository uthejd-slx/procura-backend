from __future__ import annotations

from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "display_name",
            "phone_number",
            "job_title",
            "avatar_url",
            "notifications_email_enabled",
            "roles",
            "updated_at",
        )
        read_only_fields = ("roles", "updated_at")
