from __future__ import annotations

from datetime import datetime, time

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from boms.permissions import has_role
from core.pagination import StandardResultsSetPagination

from .models import Bill
from .serializers import BillCreateSerializer, BillSerializer


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


class BillViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = Bill.objects.select_related("bom", "purchase_order", "created_by", "approved_by")
        if not (has_role(user, "admin") or has_role(user, "procurement")):
            qs = qs.filter(Q(created_by=user) | Q(bom__owner=user) | Q(purchase_order__created_by=user))

        params = self.request.query_params
        status_param = params.get("status")
        if status_param:
            qs = qs.filter(status__in=[s.strip().upper() for s in status_param.split(",") if s.strip()])

        vendor = params.get("vendor")
        if vendor:
            qs = qs.filter(vendor_name__icontains=vendor)

        bom_id = params.get("bom_id")
        if bom_id:
            try:
                qs = qs.filter(bom_id=int(bom_id))
            except Exception:
                pass

        po_id = params.get("purchase_order_id")
        if po_id:
            try:
                qs = qs.filter(purchase_order_id=int(po_id))
            except Exception:
                pass

        created_from = _parse_dt(params.get("created_from"))
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        created_to = _parse_dt(params.get("created_to"), end_of_day=True)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)

        return qs.order_by("-updated_at")

    def get_serializer_class(self):
        if self.action == "create":
            return BillCreateSerializer
        return BillSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status=Bill.Status.DRAFT)

    def update(self, request, *args, **kwargs):
        bill: Bill = self.get_object()
        if bill.created_by_id != request.user.id and not has_role(request.user, "procurement") and not has_role(request.user, "admin"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if bill.status not in {Bill.Status.DRAFT, Bill.Status.REJECTED}:
            return Response({"detail": "Bill is not editable."}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)
