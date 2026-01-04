from __future__ import annotations

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "title", "level", "read_at", "created_at")
    list_filter = ("level", "read_at", "created_at")
    search_fields = ("title", "body", "recipient__email")
    ordering = ("-created_at",)
