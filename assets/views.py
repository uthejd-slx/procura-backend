from __future__ import annotations

from django.db.models import Q
from rest_framework import permissions, viewsets

from boms.permissions import has_role
from core.pagination import StandardResultsSetPagination

from .models import Asset
from .permissions import IsProcurementOrAdmin
from .serializers import AssetSerializer, AssetUpdateSerializer


class AssetViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [permissions.IsAuthenticated(), IsProcurementOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Asset.objects.select_related("source_bom_item", "source_po_item", "created_by")
        if not (has_role(user, "admin") or has_role(user, "procurement")):
            qs = qs.filter(Q(source_bom_item__bom__owner=user) | Q(created_by=user))

        params = self.request.query_params
        status_param = params.get("status")
        if status_param:
            statuses = [s.strip().upper() for s in status_param.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        bom_id = params.get("bom_id")
        if bom_id:
            try:
                qs = qs.filter(source_bom_item__bom_id=int(bom_id))
            except Exception:
                pass

        po_id = params.get("purchase_order_id")
        if po_id:
            try:
                qs = qs.filter(source_po_item__purchase_order_id=int(po_id))
            except Exception:
                pass

        category = params.get("category")
        if category:
            qs = qs.filter(category__icontains=category)

        vendor = params.get("vendor")
        if vendor:
            qs = qs.filter(vendor__icontains=vendor)

        search_term = params.get("search") or params.get("q")
        if search_term:
            qs = qs.filter(Q(name__icontains=search_term) | Q(description__icontains=search_term))

        return qs.order_by("-created_at")

    def get_serializer_class(self):
        if self.action in {"update", "partial_update"}:
            return AssetUpdateSerializer
        return AssetSerializer
