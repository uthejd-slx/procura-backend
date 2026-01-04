from __future__ import annotations

from rest_framework import serializers

from .models import CatalogItem


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = (
            "id",
            "owner",
            "name",
            "description",
            "category",
            "vendor_name",
            "vendor_url",
            "currency",
            "unit_price",
            "tax_percent",
            "data",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")


class CatalogItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = (
            "name",
            "description",
            "category",
            "vendor_name",
            "vendor_url",
            "currency",
            "unit_price",
            "tax_percent",
            "data",
        )

