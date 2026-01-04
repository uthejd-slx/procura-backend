from __future__ import annotations

from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "status", "user", "created_at")
    list_filter = ("category", "status")
    search_fields = ("message", "user__email")
