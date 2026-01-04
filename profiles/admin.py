from __future__ import annotations

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "job_title", "notifications_email_enabled", "roles", "updated_at")
    search_fields = ("user__email", "display_name", "job_title")
