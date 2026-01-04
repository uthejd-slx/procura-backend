from __future__ import annotations

from django.conf import settings
from django.db import models


class CatalogItem(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="catalog_items")
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=200, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True)
    vendor_url = models.URLField(blank=True)
    currency = models.CharField(max_length=20, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "name"]),
            models.Index(fields=["vendor_name"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return self.name

# Create your models here.
