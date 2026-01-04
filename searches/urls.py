from __future__ import annotations

from rest_framework.routers import DefaultRouter

from .views import SearchHistoryViewSet


router = DefaultRouter()
router.register(r"search/history", SearchHistoryViewSet, basename="search-history")

urlpatterns = router.urls
