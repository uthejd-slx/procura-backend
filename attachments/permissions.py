from __future__ import annotations

from rest_framework.permissions import BasePermission

from boms.permissions import has_role


class CanAccessAttachment(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.owner_id == request.user.id:
            return True
        if has_role(request.user, "admin") or has_role(request.user, "procurement"):
            return True
        if obj.bom_id and getattr(obj.bom, "owner_id", None) == request.user.id:
            return True
        if obj.purchase_order_id:
            po = obj.purchase_order
            if po and (po.created_by_id == request.user.id or getattr(po.bom, "owner_id", None) == request.user.id):
                return True
        if obj.bill_id:
            bill = obj.bill
            if bill:
                if bill.created_by_id == request.user.id:
                    return True
                if getattr(bill.bom, "owner_id", None) == request.user.id:
                    return True
                if getattr(bill.purchase_order, "created_by_id", None) == request.user.id:
                    return True
        return False
