from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import AttachmentViewSet


router = DefaultRouter()
router.register(r"attachments", AttachmentViewSet, basename="attachments")

urlpatterns = router.urls

