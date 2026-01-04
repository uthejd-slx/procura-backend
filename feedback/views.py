from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from accounts.permissions import IsAdminRole
from core.pagination import StandardResultsSetPagination

from .models import Feedback
from .serializers import FeedbackAdminUpdateSerializer, FeedbackCreateSerializer, FeedbackSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if IsAdminRole().has_permission(self.request, self):
            return Feedback.objects.all().order_by("-created_at")
        return Feedback.objects.filter(user=user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return FeedbackCreateSerializer
        if self.action in {"update", "partial_update"}:
            return FeedbackAdminUpdateSerializer
        return FeedbackSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        if not IsAdminRole().has_permission(request, self):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not IsAdminRole().has_permission(request, self):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not IsAdminRole().has_permission(request, self):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
