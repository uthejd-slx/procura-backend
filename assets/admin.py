from __future__ import annotations

from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "quantity", "transferred_quantity", "vendor", "created_at")
    search_fields = ("name", "vendor")
    list_filter = ("status", "category")
