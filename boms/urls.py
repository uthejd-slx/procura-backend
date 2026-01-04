from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import (
    BomEventViewSet,
    BomItemViewSet,
    BomTemplateViewSet,
    BomViewSet,
    ProcurementActionsViewSet,
    ProcurementApprovalViewSet,
)


router = DefaultRouter()
router.register(r"bom-templates", BomTemplateViewSet, basename="bom-templates")
router.register(r"boms", BomViewSet, basename="boms")
router.register(r"bom-items", BomItemViewSet, basename="bom-items")
router.register(r"procurement-approvals", ProcurementApprovalViewSet, basename="procurement-approvals")
router.register(r"bom-events", BomEventViewSet, basename="bom-events")
router.register(r"procurement-actions", ProcurementActionsViewSet, basename="procurement-actions")

urlpatterns = router.urls
