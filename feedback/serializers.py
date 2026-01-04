from __future__ import annotations

from rest_framework import serializers

from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = (
            "id",
            "user",
            "category",
            "message",
            "page_url",
            "rating",
            "metadata",
            "status",
            "admin_note",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "status",
            "admin_note",
            "created_at",
            "updated_at",
        )


class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ("category", "message", "page_url", "rating", "metadata")

    def validate_rating(self, value):
        if value is None:
            return value
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class FeedbackAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ("status", "admin_note")
