from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import PartnerCompanyViewSet, TransferViewSet


router = DefaultRouter()
router.register(r"partners", PartnerCompanyViewSet, basename="partners")
router.register(r"transfers", TransferViewSet, basename="transfers")

urlpatterns = router.urls

