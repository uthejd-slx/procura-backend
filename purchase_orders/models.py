from __future__ import annotations

from django.conf import settings
from django.db import models


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        PARTIAL = "PARTIAL", "Partial"
        RECEIVED = "RECEIVED", "Received"
        CANCELED = "CANCELED", "Canceled"

    bom = models.ForeignKey(
        "boms.Bom", on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_orders"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="purchase_orders"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["vendor_name"]),
        ]

    def __str__(self) -> str:
        return self.po_number or f"PO-{self.pk}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    bom_item = models.ForeignKey("boms.BomItem", on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=20, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=200, blank=True)
    link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)

    ordered_at = models.DateTimeField(null=True, blank=True)
    eta_date = models.DateField(null=True, blank=True)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    received_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["purchase_order", "name"]),
            models.Index(fields=["eta_date"]),
        ]

    @property
    def is_fully_received(self) -> bool:
        return self.received_quantity >= self.quantity

    def __str__(self) -> str:
        return f"PO Item {self.pk} ({self.name})"

# Create your models here.
