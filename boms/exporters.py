from __future__ import annotations

import csv
import json
from io import StringIO



def _clean_text(value: object, max_len: int | None = None) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if max_len and len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _bom_base_row(bom) -> dict:
    owner_email = getattr(getattr(bom, "owner", None), "email", "")
    return {
        "bom_id": bom.pk,
        "bom_title": bom.title,
        "bom_project": bom.project or "",
        "bom_status": bom.status,
        "bom_owner_email": owner_email,
        "bom_created_at": bom.created_at.isoformat() if bom.created_at else "",
        "bom_updated_at": bom.updated_at.isoformat() if bom.updated_at else "",
        "bom_data": json.dumps(bom.data or {}, ensure_ascii=True),
    }


def export_bom_csv(bom) -> bytes:
    fieldnames = [
        "bom_id",
        "bom_title",
        "bom_project",
        "bom_status",
        "bom_owner_email",
        "bom_created_at",
        "bom_updated_at",
        "bom_data",
        "item_id",
        "item_name",
        "item_description",
        "item_quantity",
        "item_unit",
        "item_currency",
        "item_unit_price",
        "item_tax_percent",
        "item_vendor",
        "item_category",
        "item_link",
        "item_notes",
        "item_data",
        "item_signoff_status",
        "item_signoff_assignee_email",
        "item_ordered_at",
        "item_eta_date",
        "item_received_quantity",
        "item_received_at",
    ]

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    base = _bom_base_row(bom)
    items = list(bom.items.all())
    if not items:
        writer.writerow({**base})
    else:
        for item in items:
            assignee_email = getattr(getattr(item, "signoff_assignee", None), "email", "")
            row = {
                **base,
                "item_id": item.id,
                "item_name": item.name,
                "item_description": item.description,
                "item_quantity": item.quantity,
                "item_unit": item.unit,
                "item_currency": item.currency,
                "item_unit_price": item.unit_price,
                "item_tax_percent": item.tax_percent,
                "item_vendor": item.vendor,
                "item_category": item.category,
                "item_link": item.link,
                "item_notes": item.notes,
                "item_data": json.dumps(item.data or {}, ensure_ascii=True),
                "item_signoff_status": item.signoff_status,
                "item_signoff_assignee_email": assignee_email,
                "item_ordered_at": item.ordered_at.isoformat() if item.ordered_at else "",
                "item_eta_date": item.eta_date.isoformat() if item.eta_date else "",
                "item_received_quantity": item.received_quantity,
                "item_received_at": item.received_at.isoformat() if item.received_at else "",
            }
            writer.writerow(row)

    return output.getvalue().encode("utf-8")


def export_bom_pdf(bom) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError("fpdf2 is required for PDF exports.") from exc
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _clean_text(f"BOM #{bom.pk} - {bom.title}", 120), ln=1)

    pdf.set_font("Helvetica", "", 10)
    owner_email = getattr(getattr(bom, "owner", None), "email", "")
    pdf.cell(0, 6, _clean_text(f"Project: {bom.project or '-'}"), ln=1)
    pdf.cell(0, 6, _clean_text(f"Status: {bom.status}"), ln=1)
    pdf.cell(0, 6, _clean_text(f"Owner: {owner_email or '-'}"), ln=1)
    pdf.cell(0, 6, _clean_text(f"Created: {bom.created_at.isoformat() if bom.created_at else '-'}"), ln=1)
    pdf.cell(0, 6, _clean_text(f"Updated: {bom.updated_at.isoformat() if bom.updated_at else '-'}"), ln=1)

    bom_data = bom.data or {}
    if bom_data:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "BOM Data", ln=1)
        pdf.set_font("Helvetica", "", 9)
        for key, value in bom_data.items():
            pdf.multi_cell(0, 5, _clean_text(f"{key}: {value}", 200))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Items", ln=1)
    pdf.set_font("Helvetica", "B", 8)

    columns = [
        ("Item", 40),
        ("Qty", 12),
        ("Unit", 12),
        ("Currency", 14),
        ("Unit Price", 18),
        ("Tax %", 10),
        ("Vendor", 28),
        ("Category", 24),
        ("Link", 50),
        ("Data", 60),
    ]

    for title, width in columns:
        pdf.cell(width, 6, title, border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for item in bom.items.all():
        values = [
            _clean_text(item.name, 48),
            _clean_text(item.quantity, 12),
            _clean_text(item.unit, 10),
            _clean_text(item.currency, 10),
            _clean_text(item.unit_price, 12),
            _clean_text(item.tax_percent, 8),
            _clean_text(item.vendor, 24),
            _clean_text(item.category, 20),
            _clean_text(item.link, 60),
            _clean_text(json.dumps(item.data or {}, ensure_ascii=True), 90),
        ]
        for (title, width), value in zip(columns, values):
            pdf.cell(width, 6, value, border=1)
        pdf.ln()

    output = pdf.output(dest="S")
    if isinstance(output, bytes):
        return output
    return output.encode("latin-1")
