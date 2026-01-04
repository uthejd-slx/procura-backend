from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from boms.permissions import has_role
from core.pagination import StandardResultsSetPagination

from assets.models import Asset
from assets.services import apply_transfer_quantities

from .models import PartnerCompany, Transfer, TransferItem
from .permissions import IsProcurementOrAdmin
from .serializers import (
    PartnerCompanySerializer,
    TransferCreateSerializer,
    TransferItemCreateSerializer,
    TransferItemSerializer,
    TransferSerializer,
)


class PartnerCompanyViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    queryset = PartnerCompany.objects.all().order_by("name")
    serializer_class = PartnerCompanySerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [permissions.IsAuthenticated(), IsProcurementOrAdmin()]
        return super().get_permissions()


class TransferViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = Transfer.objects.select_related("partner", "created_by", "approved_by")
        if not (has_role(user, "admin") or has_role(user, "procurement")):
            qs = qs.filter(created_by=user)
        return qs.order_by("-updated_at")

    def get_serializer_class(self):
        if self.action == "create":
            return TransferCreateSerializer
        return TransferSerializer

    def perform_create(self, serializer):
        if not (has_role(self.request.user, "admin") or has_role(self.request.user, "procurement")):
            raise permissions.PermissionDenied("Not allowed.")
        serializer.save(created_by=self.request.user, status=Transfer.Status.DRAFT)

    @action(detail=True, methods=["post"], url_path="items")
    def add_item(self, request, pk=None):
        transfer: Transfer = self.get_object()
        if not (has_role(request.user, "admin") or has_role(request.user, "procurement")):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        serializer = TransferItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset: Asset = serializer.validated_data["asset"]
        qty: Decimal = serializer.validated_data["quantity"]
        if qty <= 0:
            return Response({"detail": "Quantity must be positive."}, status=status.HTTP_400_BAD_REQUEST)
        if asset.available_quantity < qty:
            return Response({"detail": "Not enough available quantity."}, status=status.HTTP_400_BAD_REQUEST)
        item = TransferItem.objects.create(transfer=transfer, **serializer.validated_data)
        return Response(TransferItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        transfer: Transfer = self.get_object()
        if not (has_role(request.user, "admin") or has_role(request.user, "procurement")):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        transfer.status = Transfer.Status.SUBMITTED
        transfer.save(update_fields=["status"])
        return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        transfer: Transfer = self.get_object()
        if not has_role(request.user, "admin") and not has_role(request.user, "approver"):
            return Response({"detail": "Approver role required."}, status=status.HTTP_403_FORBIDDEN)
        transfer.status = Transfer.Status.APPROVED
        transfer.approved_by = request.user
        transfer.approved_at = timezone.now()
        transfer.save(update_fields=["status", "approved_by", "approved_at"])
        return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        transfer: Transfer = self.get_object()
        if not (has_role(request.user, "admin") or has_role(request.user, "procurement")):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        items = list(transfer.items.select_related("asset"))
        with transaction.atomic():
            apply_transfer_quantities(
                assets_and_qty=[(item.asset, Decimal(str(item.quantity))) for item in items]
            )
            transfer.status = Transfer.Status.COMPLETED
            transfer.completed_at = timezone.now()
            transfer.save(update_fields=["status", "completed_at"])
        return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        transfer: Transfer = self.get_object()
        if not (has_role(request.user, "admin") or has_role(request.user, "procurement")):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        transfer.status = Transfer.Status.CANCELED
        transfer.save(update_fields=["status"])
        return Response(TransferSerializer(transfer).data, status=status.HTTP_200_OK)
