from __future__ import annotations

from django.contrib import admin

from .models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "file_name", "owner", "bom", "purchase_order", "created_at")
    search_fields = ("file_name", "owner__email")
