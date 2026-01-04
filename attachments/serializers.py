from __future__ import annotations

from rest_framework import serializers

from .models import Attachment


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            "id",
            "owner",
            "file",
            "file_url",
            "file_name",
            "content_type",
            "size_bytes",
            "bom",
            "purchase_order",
            "bill",
            "created_at",
        )
        read_only_fields = ("id", "owner", "file_url", "file_name", "content_type", "size_bytes", "created_at")

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return ""
        url = obj.file.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class AttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ("file", "bom", "purchase_order", "bill")
