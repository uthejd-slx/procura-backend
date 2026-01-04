from __future__ import annotations

from django.contrib import admin

from .models import PartnerCompany, Transfer, TransferItem


class TransferItemInline(admin.TabularInline):
    model = TransferItem
    extra = 0


@admin.register(PartnerCompany)
class PartnerCompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "contact_email", "updated_at")
    search_fields = ("name", "contact_email")


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("id", "partner", "status", "created_by", "updated_at")
    list_filter = ("status",)
    inlines = [TransferItemInline]


@admin.register(TransferItem)
class TransferItemAdmin(admin.ModelAdmin):
    list_display = ("id", "transfer", "asset", "quantity")
