from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from boms.permissions import has_role
from core.pagination import StandardResultsSetPagination

from .models import PurchaseOrder, PurchaseOrderItem
from .permissions import IsProcurementStrict
from .serializers import (
    CreatePurchaseOrderItemSerializer,
    CreatePurchaseOrderSerializer,
    PurchaseOrderItemSerializer,
    PurchaseOrderSerializer,
    ReceiveItemsSerializer,
)
from .services import generate_po_number, recompute_po_status


def _parse_dt(value: str | None, *, end_of_day: bool = False):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is not None:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    d = parse_date(value)
    if not d:
        return None
    t = time.max if end_of_day else time.min
    dt = datetime.combine(d, t)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "add_item", "mark_sent", "cancel", "receive"}:
            return [permissions.IsAuthenticated(), IsProcurementStrict()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = PurchaseOrder.objects.all()
        if not (has_role(user, "admin") or has_role(user, "procurement")):
            qs = qs.filter(models.Q(created_by=user) | models.Q(bom__owner=user))

        params = self.request.query_params
        status_param = params.get("status")
        if status_param:
            statuses = [s.strip().upper() for s in status_param.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        bom_id = params.get("bom_id")
        if bom_id:
            try:
                qs = qs.filter(bom_id=int(bom_id))
            except Exception:
                pass

        vendor = params.get("vendor")
        if vendor:
            qs = qs.filter(vendor_name__icontains=vendor)

        category = params.get("category")
        if category:
            qs = qs.filter(items__category__icontains=category)

        search_term = params.get("search") or params.get("q")
        if search_term:
            qs = qs.filter(Q(po_number__icontains=search_term) | Q(vendor_name__icontains=search_term))

        created_from = _parse_dt(params.get("created_from"))
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        created_to = _parse_dt(params.get("created_to"), end_of_day=True)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)

        updated_from = _parse_dt(params.get("updated_from"))
        if updated_from:
            qs = qs.filter(updated_at__gte=updated_from)
        updated_to = _parse_dt(params.get("updated_to"), end_of_day=True)
        if updated_to:
            qs = qs.filter(updated_at__lte=updated_to)

        return qs.distinct().order_by("-updated_at")

    def get_serializer_class(self):
        if self.action == "create":
            return CreatePurchaseOrderSerializer
        return PurchaseOrderSerializer

    def perform_create(self, serializer):
        po = serializer.save(created_by=self.request.user, status=PurchaseOrder.Status.DRAFT)
        if not po.po_number:
            po.po_number = generate_po_number(po)
            po.save(update_fields=["po_number"])

    @action(detail=True, methods=["post"], url_path="items")
    def add_item(self, request, pk=None):
        po: PurchaseOrder = self.get_object()
        serializer = CreatePurchaseOrderItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = PurchaseOrderItem.objects.create(purchase_order=po, ordered_at=timezone.now(), **serializer.validated_data)
        return Response(PurchaseOrderItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-sent")
    def mark_sent(self, request, pk=None):
        po: PurchaseOrder = self.get_object()
        if po.status == PurchaseOrder.Status.CANCELED:
            return Response({"detail": "PO is canceled."}, status=status.HTTP_400_BAD_REQUEST)
        po.status = PurchaseOrder.Status.SENT
        po.save(update_fields=["status"])
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        po: PurchaseOrder = self.get_object()
        po.status = PurchaseOrder.Status.CANCELED
        po.save(update_fields=["status"])
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        po: PurchaseOrder = self.get_object()
        serializer = ReceiveItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines = serializer.validated_data["lines"]

        with transaction.atomic():
            updated_ids: list[int] = []
            for line in lines:
                item_id = line["item_id"]
                qty: Decimal = line["quantity_received"]
                item = po.items.filter(id=item_id).first()
                if not item:
                    continue
                item.received_quantity = item.received_quantity + qty
                item.received_at = timezone.now()
                item.save(update_fields=["received_quantity", "received_at"])
                updated_ids.append(item.id)

            recompute_po_status(po)

        if updated_ids:
            from assets.services import convert_po_items_to_assets

            items = list(po.items.filter(id__in=updated_ids))
            convert_po_items_to_assets(items=items, actor=request.user)

        return Response({"detail": "Receipt recorded.", "item_ids": updated_ids}, status=status.HTTP_200_OK)
