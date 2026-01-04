from __future__ import annotations

from rest_framework import serializers

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    available_quantity = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)

    class Meta:
        model = Asset
        fields = (
            "id",
            "source_bom_item",
            "source_po_item",
            "created_by",
            "name",
            "description",
            "category",
            "vendor",
            "quantity",
            "transferred_quantity",
            "available_quantity",
            "unit",
            "status",
            "data",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "transferred_quantity",
            "available_quantity",
            "created_at",
        )


class AssetUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ("name", "description", "category", "vendor", "quantity", "unit", "status", "data")
