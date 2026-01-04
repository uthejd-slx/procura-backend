from __future__ import annotations

from django.contrib import admin

from .models import CatalogItem


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "vendor_name", "category", "updated_at")
    search_fields = ("name", "vendor_name", "category", "owner__email")
    list_filter = ("category",)
