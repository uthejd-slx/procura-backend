from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import CatalogItemViewSet


router = DefaultRouter()
router.register(r"catalog-items", CatalogItemViewSet, basename="catalog-items")

urlpatterns = router.urls

