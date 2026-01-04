from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .models import Bom, BomCollaborator, BomEvent, BomItem, BomTemplate, ProcurementApproval, ProcurementApprovalRequest


class BomTemplateSerializer(serializers.ModelSerializer):
    is_global = serializers.BooleanField(read_only=True)

    class Meta:
        model = BomTemplate
        fields = ("id", "name", "description", "schema", "owner", "is_global", "created_at", "updated_at")
        read_only_fields = ("id", "owner", "is_global", "created_at", "updated_at")


class BomCollaboratorSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_display_name = serializers.CharField(source="user.profile.display_name", read_only=True)
    added_by_email = serializers.EmailField(source="added_by.email", read_only=True)

    class Meta:
        model = BomCollaborator
        fields = ("id", "bom", "user", "user_email", "user_display_name", "added_by", "added_by_email", "added_at")
        read_only_fields = ("id", "bom", "user", "user_email", "user_display_name", "added_by", "added_by_email", "added_at")


class BomItemSerializer(serializers.ModelSerializer):
    is_fully_received = serializers.BooleanField(read_only=True)

    class Meta:
        model = BomItem
        fields = (
            "id",
            "bom",
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
            "signoff_assignee",
            "signoff_status",
            "signoff_comment",
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
            "bom",
            "ordered_at",
            "received_quantity",
            "received_at",
            "is_fully_received",
            "created_at",
            "updated_at",
        )


class BomSerializer(serializers.ModelSerializer):
    items = BomItemSerializer(many=True, read_only=True)

    class Meta:
        model = Bom
        fields = (
            "id",
            "owner",
            "template",
            "title",
            "project",
            "status",
            "data",
            "cancel_comment",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "status", "cancel_comment", "created_at", "updated_at")


class BomEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomEvent
        fields = ("id", "bom", "actor", "event_type", "message", "data", "created_at")
        read_only_fields = fields


class ProcurementApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementApproval
        fields = ("id", "request", "approver", "status", "comment", "decided_at")
        read_only_fields = ("id", "request", "approver", "decided_at")


class ProcurementApprovalRequestSerializer(serializers.ModelSerializer):
    approvals = ProcurementApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = ProcurementApprovalRequest
        fields = ("id", "bom", "requested_by", "status", "comment", "created_at", "decided_at", "approvals")
        read_only_fields = ("id", "bom", "requested_by", "status", "created_at", "decided_at", "approvals")


class CreateBomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bom
        fields = ("template", "title", "project", "data")


class CreateBomItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomItem
        fields = (
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
        )


class RequestSignoffSerializer(serializers.Serializer):
    assignee_id = serializers.IntegerField()
    item_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    comment = serializers.CharField(required=False, allow_blank=True)


class DecideSignoffSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[BomItem.SignoffStatus.APPROVED, BomItem.SignoffStatus.NEEDS_CHANGES])
    comment = serializers.CharField(required=False, allow_blank=True)


class RequestProcurementApprovalSerializer(serializers.Serializer):
    approver_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    comment = serializers.CharField(required=False, allow_blank=True)


class DecideProcurementApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[ProcurementApproval.Status.APPROVED, ProcurementApproval.Status.NEEDS_CHANGES]
    )
    comment = serializers.CharField(required=False, allow_blank=True)


class CancelFlowSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class ReceiveLineSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    quantity_received = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))


class ReceiveItemsSerializer(serializers.Serializer):
    lines = ReceiveLineSerializer(many=True, allow_empty=False)
    comment = serializers.CharField(required=False, allow_blank=True)
