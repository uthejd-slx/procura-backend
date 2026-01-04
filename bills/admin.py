from __future__ import annotations

from django.contrib import admin

from .models import Bill


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "vendor_name", "status", "amount", "currency", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "vendor_name")
