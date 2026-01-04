from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import PurchaseOrderViewSet


router = DefaultRouter()
router.register(r"purchase-orders", PurchaseOrderViewSet, basename="purchase-orders")

urlpatterns = router.urls

