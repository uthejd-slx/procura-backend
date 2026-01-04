from __future__ import annotations

from decimal import Decimal

from .models import Asset


def _coerce_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def convert_bom_items_to_assets(*, items, actor=None) -> int:
    created = 0
    for item in items:
        if not item.is_fully_received:
            continue
        if Asset.objects.filter(source_bom_item=item).exists():
            continue
        Asset.objects.create(
            source_bom_item=item,
            created_by=actor,
            name=item.name,
            description=item.description,
            category=getattr(item, "category", ""),
            vendor=item.vendor,
            quantity=_coerce_decimal(item.quantity),
            unit=item.unit,
            data={"bom_id": item.bom_id, "bom_item_id": item.id},
        )
        created += 1
    return created


def convert_po_items_to_assets(*, items, actor=None) -> int:
    created = 0
    for item in items:
        if not item.is_fully_received:
            continue
        if Asset.objects.filter(source_po_item=item).exists():
            continue
        Asset.objects.create(
            source_po_item=item,
            created_by=actor,
            name=item.name,
            description=item.description,
            category=getattr(item, "category", ""),
            vendor=item.vendor,
            quantity=_coerce_decimal(item.quantity),
            unit=item.unit,
            data={"purchase_order_id": item.purchase_order_id, "purchase_order_item_id": item.id},
        )
        created += 1
    return created


def apply_transfer_quantities(*, assets_and_qty: list[tuple[Asset, Decimal]]) -> None:
    for asset, qty in assets_and_qty:
        asset.transferred_quantity = asset.transferred_quantity + qty
        if asset.transferred_quantity >= asset.quantity:
            asset.status = Asset.Status.TRANSFERRED
        asset.save(update_fields=["transferred_quantity", "status"])
