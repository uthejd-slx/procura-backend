from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    is_fully_received = serializers.BooleanField(read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = (
            "id",
            "purchase_order",
            "bom_item",
            "name",
            "description",
            "quantity",
            "unit",
            "currency",
            "unit_price",
            "tax_percent",
            "vendor",
            "category",
            "link",
            "notes",
            "data",
            "ordered_at",
            "eta_date",
            "received_quantity",
            "received_at",
            "is_fully_received",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "purchase_order",
            "ordered_at",
            "received_quantity",
            "received_at",
            "is_fully_received",
            "created_at",
            "updated_at",
        )


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id",
            "bom",
            "created_by",
            "status",
            "po_number",
            "vendor_name",
            "currency",
            "notes",
            "data",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "status", "created_at", "updated_at")


class CreatePurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ("bom", "po_number", "vendor_name", "currency", "notes", "data")


class CreatePurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = (
            "bom_item",
            "name",
            "description",
            "quantity",
            "unit",
            "currency",
            "unit_price",
            "tax_percent",
            "vendor",
            "category",
            "link",
            "notes",
            "data",
            "eta_date",
        )


class ReceiveLineSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    quantity_received = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))


class ReceiveItemsSerializer(serializers.Serializer):
    lines = ReceiveLineSerializer(many=True, allow_empty=False)
    comment = serializers.CharField(required=False, allow_blank=True)
