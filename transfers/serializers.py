from __future__ import annotations

from rest_framework import serializers

from assets.serializers import AssetSerializer

from .models import PartnerCompany, Transfer, TransferItem


class PartnerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerCompany
        fields = ("id", "name", "contact_email", "contact_phone", "address", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class TransferItemSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)

    class Meta:
        model = TransferItem
        fields = ("id", "transfer", "asset", "quantity", "notes", "created_at")
        read_only_fields = ("id", "transfer", "created_at")


class TransferSerializer(serializers.ModelSerializer):
    items = TransferItemSerializer(many=True, read_only=True)

    class Meta:
        model = Transfer
        fields = (
            "id",
            "partner",
            "created_by",
            "status",
            "notes",
            "approved_by",
            "approved_at",
            "completed_at",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_by", "approved_by", "approved_at", "completed_at", "created_at", "updated_at")


class TransferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfer
        fields = ("partner", "notes")


class TransferItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferItem
        fields = ("asset", "quantity", "notes")
