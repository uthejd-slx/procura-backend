from __future__ import annotations

from django.db.models import Q
from rest_framework import permissions, viewsets

from boms.permissions import has_role
from core.pagination import StandardResultsSetPagination

from .models import CatalogItem
from .serializers import CatalogItemCreateSerializer, CatalogItemSerializer


class CatalogItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if has_role(user, "admin") or has_role(user, "procurement"):
            qs = CatalogItem.objects.all()
        else:
            qs = CatalogItem.objects.filter(owner=user)

        params = self.request.query_params
        search_term = params.get("search") or params.get("q")
        if search_term:
            qs = qs.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(vendor_name__icontains=search_term)
                | Q(category__icontains=search_term)
            )

        category = params.get("category")
        if category:
            qs = qs.filter(category__icontains=category)

        vendor = params.get("vendor")
        if vendor:
            qs = qs.filter(vendor_name__icontains=vendor)

        return qs.order_by("-updated_at")

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return CatalogItemCreateSerializer
        return CatalogItemSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
