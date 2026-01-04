from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from .models import PurchaseOrder, PurchaseOrderItem


def generate_po_number(po: PurchaseOrder) -> str:
    prefix = getattr(settings, "PO_NUMBER_PREFIX", "PO-")
    padding = int(getattr(settings, "PO_NUMBER_PADDING", 5))
    date_part = po.created_at.strftime("%Y%m%d") if po.created_at else timezone.now().strftime("%Y%m%d")
    return f"{prefix}{date_part}-{po.id:0{padding}d}"


def recompute_po_status(po: PurchaseOrder) -> None:
    if po.status == PurchaseOrder.Status.CANCELED:
        return
    items = list(po.items.all())
    if not items:
        return
    if all(i.is_fully_received for i in items):
        po.status = PurchaseOrder.Status.RECEIVED
        po.save(update_fields=["status"])
        return
    if any(i.received_quantity > 0 for i in items):
        po.status = PurchaseOrder.Status.PARTIAL
        po.save(update_fields=["status"])
        return
