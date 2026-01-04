from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import BillViewSet


router = DefaultRouter()
router.register(r"bills", BillViewSet, basename="bills")

urlpatterns = router.urls

