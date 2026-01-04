from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.roles import has_role


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and has_role(request.user, "admin"))

