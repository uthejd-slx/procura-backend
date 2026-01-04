from __future__ import annotations

from django.conf import settings
from django.db import models


class Attachment(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/%d")
    file_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.BigIntegerField(default=0)

    bom = models.ForeignKey("boms.Bom", on_delete=models.SET_NULL, null=True, blank=True, related_name="attachments")
    purchase_order = models.ForeignKey(
        "purchase_orders.PurchaseOrder", on_delete=models.SET_NULL, null=True, blank=True, related_name="attachments"
    )
    bill = models.ForeignKey("bills.Bill", on_delete=models.SET_NULL, null=True, blank=True, related_name="attachments")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "created_at"]),
            models.Index(fields=["bom"]),
            models.Index(fields=["purchase_order"]),
        ]

    def __str__(self) -> str:
        return self.file_name or f"Attachment {self.pk}"

# Create your models here.
