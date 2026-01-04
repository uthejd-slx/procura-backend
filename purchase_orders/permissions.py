from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.roles import has_role, has_role_strict


class IsProcurementStrict(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and has_role_strict(request.user, "procurement"))


class CanViewPurchaseOrders(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (has_role(request.user, "procurement") or has_role(request.user, "admin")))
