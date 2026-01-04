from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models


class Asset(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        DISPOSED = "DISPOSED", "Disposed"

    source_bom_item = models.OneToOneField(
        "boms.BomItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="asset"
    )
    source_po_item = models.OneToOneField(
        "purchase_orders.PurchaseOrderItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="asset"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assets_created"
    )

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=200, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    transferred_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    unit = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
        ]

    @property
    def available_quantity(self) -> Decimal:
        return self.quantity - self.transferred_quantity

    def __str__(self) -> str:
        return self.name

# Create your models here.
