from __future__ import annotations

from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "po_number", "status", "vendor_name", "created_by", "updated_at")
    search_fields = ("po_number", "vendor_name", "created_by__email")
    list_filter = ("status",)
    inlines = [PurchaseOrderItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "purchase_order", "name", "quantity", "received_quantity", "eta_date")
    search_fields = ("name", "purchase_order__po_number")
