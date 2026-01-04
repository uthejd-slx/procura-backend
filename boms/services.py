from __future__ import annotations

from django.contrib.auth import get_user_model

from boms.models import Bom, BomEvent, BomItem, ProcurementApprovalRequest
from core.roles import has_role_strict
from notifications.services import notify_user


def log_event(*, bom: Bom, actor, event_type: str, message: str = "", data: dict | None = None) -> None:
    BomEvent.objects.create(bom=bom, actor=actor, event_type=event_type, message=message, data=data or {})


def recompute_bom_status(bom: Bom) -> None:
    if bom.status in {Bom.Status.CANCELED, Bom.Status.COMPLETED}:
        return

    items = list(bom.items.all())
    if any(i.signoff_status == BomItem.SignoffStatus.REQUESTED for i in items):
        if bom.status != Bom.Status.SIGNOFF_PENDING:
            bom.status = Bom.Status.SIGNOFF_PENDING
            bom.save(update_fields=["status"])
        return

    latest_req = bom.approval_requests.order_by("-created_at").first()
    if latest_req and latest_req.status == ProcurementApprovalRequest.Status.PENDING:
        if bom.status != Bom.Status.APPROVAL_PENDING:
            bom.status = Bom.Status.APPROVAL_PENDING
            bom.save(update_fields=["status"])
        return
    if latest_req and latest_req.status == ProcurementApprovalRequest.Status.NEEDS_CHANGES:
        if bom.status != Bom.Status.NEEDS_CHANGES:
            bom.status = Bom.Status.NEEDS_CHANGES
            bom.save(update_fields=["status"])
        return
    if latest_req and latest_req.status == ProcurementApprovalRequest.Status.APPROVED:
        if items and all(i.is_fully_received for i in items):
            bom.status = Bom.Status.COMPLETED
            bom.save(update_fields=["status"])
            return
        if any(i.received_quantity > 0 for i in items):
            bom.status = Bom.Status.RECEIVING
            bom.save(update_fields=["status"])
            return
        if any(i.ordered_at for i in items):
            bom.status = Bom.Status.ORDERED
            bom.save(update_fields=["status"])
            return
        bom.status = Bom.Status.APPROVED
        bom.save(update_fields=["status"])
        return

    if bom.status != Bom.Status.DRAFT:
        bom.status = Bom.Status.DRAFT
        bom.save(update_fields=["status"])


def notify_signoff_requested(*, bom_item: BomItem, requested_by, comment: str = "") -> None:
    if not bom_item.signoff_assignee:
        return
    notify_user(
        recipient=bom_item.signoff_assignee,
        title="Signoff requested",
        body=f"{requested_by.email} requested signoff for '{bom_item.name}' in BOM #{bom_item.bom_id}. {comment}".strip(),
        link=f"/boms/{bom_item.bom_id}",
    )


def notify_procurement_approval_requested(*, approver, bom: Bom, requested_by, comment: str = "") -> None:
    notify_user(
        recipient=approver,
        title="Procurement approval requested",
        body=f"{requested_by.email} requested procurement approval for BOM #{bom.pk}. {comment}".strip(),
        link=f"/boms/{bom.pk}",
    )


def notify_bom_needs_changes(*, bom: Bom, comment: str = "") -> None:
    notify_user(
        recipient=bom.owner,
        title="BOM needs changes",
        body=f"BOM #{bom.pk} needs changes. {comment}".strip(),
        link=f"/boms/{bom.pk}",
    )


def notify_bom_approved(*, bom: Bom) -> None:
    user_model = get_user_model()
    recipients: dict[int, tuple[object, str, str]] = {}

    def add_recipient(user, *, title: str, body: str) -> None:
        if not user:
            return
        if getattr(user, "id", None) in recipients:
            return
        recipients[user.id] = (user, title, body)

    add_recipient(
        bom.owner,
        title="BOM approved",
        body=f"BOM #{bom.pk} is approved for procurement.",
    )

    for user in user_model.objects.filter(is_active=True).select_related("profile"):
        if user.id == bom.owner_id:
            continue
        if not has_role_strict(user, "procurement"):
            continue
        add_recipient(
            user,
            title="BOM approved",
            body=f"BOM #{bom.pk} is approved and ready to order.",
        )

    for user, title, body in recipients.values():
        notify_user(
            recipient=user,
            title=title,
            body=body,
            link=f"/boms/{bom.pk}",
        )
