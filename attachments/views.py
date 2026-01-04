from __future__ import annotations

from rest_framework import permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from boms.permissions import has_role
from core.pagination import StandardResultsSetPagination

from .models import Attachment
from .permissions import CanAccessAttachment
from .serializers import AttachmentCreateSerializer, AttachmentSerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanAccessAttachment]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = Attachment.objects.all()
        if not (has_role(user, "admin") or has_role(user, "procurement")):
            qs = qs.filter(owner=user)

        params = self.request.query_params
        for key in ("bom_id", "purchase_order_id", "bill_id"):
            val = params.get(key)
            if val:
                field = key.replace("_id", "")
                try:
                    qs = qs.filter(**{f"{field}_id": int(val)})
                except Exception:
                    pass

        return qs.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return AttachmentCreateSerializer
        return AttachmentSerializer

    def perform_create(self, serializer):
        file_obj = serializer.validated_data.get("file")
        content_type = ""
        size_bytes = 0
        file_name = ""
        if file_obj is not None:
            content_type = getattr(file_obj, "content_type", "") or ""
            size_bytes = getattr(file_obj, "size", 0) or 0
            file_name = getattr(file_obj, "name", "") or ""

        serializer.save(
            owner=self.request.user,
            content_type=content_type,
            size_bytes=size_bytes,
            file_name=file_name,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            attachment = Attachment.objects.filter(id=response.data.get("id")).first()
            if attachment:
                response.data = AttachmentSerializer(attachment, context={"request": request}).data
        return response
