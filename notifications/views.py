from __future__ import annotations

import logging
from datetime import datetime, time

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.pagination import StandardResultsSetPagination

from .models import Notification
from .serializers import NotificationSerializer


logger = logging.getLogger("django")


def _parse_dt(value: str | None, *, end_of_day: bool = False):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is not None:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    d = parse_date(value)
    if not d:
        return None
    t = time.max if end_of_day else time.min
    dt = datetime.combine(d, t)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        params = self.request.query_params

        level = params.get("level")
        if level:
            levels = [l.strip().upper() for l in level.split(",") if l.strip()]
            qs = qs.filter(level__in=levels)

        unread = params.get("unread")
        if unread in {"1", "true", "True"}:
            qs = qs.filter(read_at__isnull=True)
        read = params.get("read")
        if read in {"1", "true", "True"}:
            qs = qs.filter(read_at__isnull=False)

        created_from = _parse_dt(params.get("created_from"))
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        created_to = _parse_dt(params.get("created_to"), end_of_day=True)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)

        return qs.order_by("-created_at")

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification: Notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=["read_at"])
        return Response(NotificationSerializer(notification).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(read_at__isnull=True)
        updated = qs.update(read_at=timezone.now())
        return Response({"detail": "Marked as read.", "updated": updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(read_at__isnull=True).count()
        if getattr(settings, "NOTIFICATIONS_POLL_LOG", False):
            logger.info("notifications.unread_count user_id=%s unread=%s", request.user.id, count)
        return Response({"unread": count}, status=status.HTTP_200_OK)
