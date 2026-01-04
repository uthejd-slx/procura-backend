from __future__ import annotations

from rest_framework.permissions import BasePermission

from boms.permissions import has_role


class IsProcurementOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (has_role(request.user, "procurement") or has_role(request.user, "admin")))
