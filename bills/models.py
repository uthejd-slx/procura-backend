from __future__ import annotations

from django.conf import settings
from django.db import models


class Bill(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        PAID = "PAID", "Paid"
        CANCELED = "CANCELED", "Canceled"

    title = models.CharField(max_length=200, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=20, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)

    bom = models.ForeignKey("boms.Bom", on_delete=models.SET_NULL, null=True, blank=True, related_name="bills")
    purchase_order = models.ForeignKey(
        "purchase_orders.PurchaseOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="bills"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="bills_created"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="bills_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["vendor_name"]),
        ]

    def __str__(self) -> str:
        return self.title or f"Bill {self.pk}"

# Create your models here.
