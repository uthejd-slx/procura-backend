from __future__ import annotations

from django.conf import settings
from django.db import models


class SearchHistory(models.Model):
    class Entity(models.TextChoices):
        BOM = "BOM", "BOM"
        CATALOG = "CATALOG", "Catalog"
        PO = "PO", "Purchase Order"
        RFQ = "RFQ", "RFQ"
        QUOTE = "QUOTE", "Quote"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_history")
    entity_type = models.CharField(max_length=20, choices=Entity.choices, default=Entity.OTHER)
    query = models.CharField(max_length=300, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["entity_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.entity_type}:{self.query}"

# Create your models here.
