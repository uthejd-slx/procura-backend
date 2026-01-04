from __future__ import annotations

from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(blank=True)
    notifications_email_enabled = models.BooleanField(default=False)
    roles = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile({self.user_id})"
