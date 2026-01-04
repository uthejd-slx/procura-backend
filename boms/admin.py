from __future__ import annotations

from django.contrib import admin

from .models import Bom, BomCollaborator, BomEvent, BomItem, BomTemplate, ProcurementApproval, ProcurementApprovalRequest


@admin.register(BomTemplate)
class BomTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "updated_at")
    search_fields = ("name", "owner__email")


class BomItemInline(admin.TabularInline):
    model = BomItem
    extra = 0


@admin.register(Bom)
class BomAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "status", "created_at", "updated_at")
    search_fields = ("title", "owner__email", "project")
    list_filter = ("status",)
    inlines = [BomItemInline]


@admin.register(BomItem)
class BomItemAdmin(admin.ModelAdmin):
    list_display = ("id", "bom", "name", "quantity", "signoff_status", "signoff_assignee", "received_quantity")
    search_fields = ("name", "bom__title")
    list_filter = ("signoff_status",)


@admin.register(ProcurementApprovalRequest)
class ProcurementApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "bom", "requested_by", "status", "created_at", "decided_at")
    list_filter = ("status",)


@admin.register(ProcurementApproval)
class ProcurementApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "approver", "status", "decided_at")
    list_filter = ("status",)


@admin.register(BomEvent)
class BomEventAdmin(admin.ModelAdmin):
    list_display = ("id", "bom", "event_type", "actor", "created_at")
    search_fields = ("bom__title", "event_type", "actor__email")


@admin.register(BomCollaborator)
class BomCollaboratorAdmin(admin.ModelAdmin):
    list_display = ("id", "bom", "user", "added_by", "added_at")
    search_fields = ("bom__title", "user__email", "added_by__email")
