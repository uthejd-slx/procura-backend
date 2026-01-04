from __future__ import annotations

from django.contrib import admin

from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "entity_type", "query", "created_at")
    search_fields = ("user__email", "query")
    list_filter = ("entity_type",)
