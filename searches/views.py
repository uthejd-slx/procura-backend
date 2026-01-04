from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from core.pagination import StandardResultsSetPagination

from .models import SearchHistory
from .serializers import CreateSearchHistorySerializer, SearchHistorySerializer


class SearchHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user).order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateSearchHistorySerializer
        return SearchHistorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
