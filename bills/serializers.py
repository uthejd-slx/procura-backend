from __future__ import annotations

from rest_framework import serializers

from .models import Bill


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = (
            "id",
            "title",
            "vendor_name",
            "amount",
            "currency",
            "due_date",
            "status",
            "notes",
            "data",
            "bom",
            "purchase_order",
            "created_by",
            "approved_by",
            "approved_at",
            "paid_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "created_by",
            "approved_by",
            "approved_at",
            "paid_at",
            "created_at",
            "updated_at",
        )


class BillCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ("title", "vendor_name", "amount", "currency", "due_date", "notes", "data", "bom", "purchase_order")
