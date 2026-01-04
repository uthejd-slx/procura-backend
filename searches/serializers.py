from __future__ import annotations

from rest_framework import serializers

from .models import SearchHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ("id", "entity_type", "query", "filters", "created_at")
        read_only_fields = ("id", "created_at")


class CreateSearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ("entity_type", "query", "filters")
