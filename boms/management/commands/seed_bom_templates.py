from __future__ import annotations

from django.core.management.base import BaseCommand

from boms.models import BomTemplate


def _sample_data(kind: str) -> tuple[dict, list[dict]]:
    if kind == "quick":
        return (
            {"purpose": "Quick restock for lab bench supplies and consumables."},
            [
                {
                    "name": "Jumper Wire Kit (120 pcs)",
                    "description": "Assorted jumper wires for breadboard prototyping.",
                    "quantity": 1,
                    "unit": "kit",
                    "currency": "USD",
                    "unit_price": 9.99,
                    "tax_percent": 5,
                    "vendor": "Amazon",
                    "category": "Lab Supplies",
                    "link": "https://www.amazon.com/dp/B01EV70C78",
                    "notes": "Standard 2.54mm pitch jumper wires.",
                    "data": {"link": "https://www.amazon.com/dp/B01EV70C78"},
                },
                {
                    "name": "MG Chemicals 835-P No-Clean Flux Pen",
                    "description": "Flux pen for soldering and rework.",
                    "quantity": 2,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 5.95,
                    "tax_percent": 5,
                    "vendor": "Amazon",
                    "category": "Soldering",
                    "link": "https://www.amazon.com/dp/B005T8QFTU",
                    "notes": "Keep at workbench for quick touch-ups.",
                    "data": {"link": "https://www.amazon.com/dp/B005T8QFTU"},
                },
            ],
        )
    if kind == "mid":
        return (
            {"purpose": "Board bring-up parts for pilot run."},
            [
                {
                    "name": "USB-C Receptacle 16P",
                    "description": "USB-C connector for power input.",
                    "quantity": 50,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 0.42,
                    "tax_percent": 5,
                    "vendor": "LCSC",
                    "category": "Connectors",
                    "link": "https://www.lcsc.com/product-detail/USB-Connectors_GCT-USB4085-GF-A_C298836.html",
                    "notes": "Use with USB-C PD controller.",
                    "data": {
                        "mfr": "GCT",
                        "mpn": "USB4085-GF-A",
                        "supplier_sku": "C298836",
                        "lead_time": "2-3 weeks",
                        "notes": "For USB-C power input.",
                        "link": "https://www.lcsc.com/product-detail/USB-Connectors_GCT-USB4085-GF-A_C298836.html",
                    },
                },
                {
                    "name": "STM32 Nucleo-64 Board",
                    "description": "Development board for STM32F401RE.",
                    "quantity": 5,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 12.50,
                    "tax_percent": 5,
                    "vendor": "Digi-Key",
                    "category": "Development Boards",
                    "link": "https://www.digikey.com/en/products/detail/stmicroelectronics/NUCLEO-F401RE/4869161",
                    "notes": "Used for firmware bring-up.",
                    "data": {
                        "mfr": "STMicroelectronics",
                        "mpn": "NUCLEO-F401RE",
                        "supplier_sku": "497-16190-ND",
                        "lead_time": "1-2 weeks",
                        "notes": "Include for firmware validation.",
                        "link": "https://www.digikey.com/en/products/detail/stmicroelectronics/NUCLEO-F401RE/4869161",
                    },
                },
            ],
        )
    if kind == "large":
        return (
            {
                "needed_by": "2026-02-15",
                "department": "Engineering",
                "budget_code": "ENG-PROT-2026",
                "priority": "High",
                "purpose": "Prototype run for new controller board.",
            },
            [
                {
                    "name": "TPS7A4700RGWT",
                    "description": "1A, low-noise LDO regulator.",
                    "quantity": 20,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 3.25,
                    "tax_percent": 5,
                    "vendor": "Mouser",
                    "category": "Power",
                    "link": "https://www.mouser.com/ProductDetail/Texas-Instruments/TPS7A4700RGWT",
                    "notes": "For analog rail.",
                    "data": {
                        "mfr": "Texas Instruments",
                        "mpn": "TPS7A4700RGWT",
                        "supplier_sku": "595-TPS7A4700RGWT",
                        "lead_time": "4 weeks",
                        "notes": "Use 10uF output cap.",
                        "datasheet": "https://www.ti.com/lit/ds/symlink/tps7a47.pdf",
                        "alt_part": "TPS7A4701RGWT",
                    },
                },
                {
                    "name": "GRM21BR60J226ME39L",
                    "description": "22uF 6.3V X5R 0805 capacitor.",
                    "quantity": 200,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 0.12,
                    "tax_percent": 5,
                    "vendor": "Digi-Key",
                    "category": "Passives",
                    "link": "https://www.digikey.com/en/products/detail/murata-electronics/GRM21BR60J226ME39L/4905409",
                    "notes": "Bulk decoupling.",
                    "data": {
                        "mfr": "Murata",
                        "mpn": "GRM21BR60J226ME39L",
                        "supplier_sku": "490-5523-1-ND",
                        "lead_time": "3-4 weeks",
                        "notes": "Use X5R dielectric.",
                        "datasheet": "https://www.murata.com/-/media/webrenewal/products/catalog/pdf/c02e.pdf",
                        "alt_part": "GRM21BR60J226ME39D",
                    },
                },
            ],
        )
    if kind == "embedded":
        return (
            {
                "needed_by": "2026-02-20",
                "department": "Hardware",
                "budget_code": "HW-EMB-2026",
                "priority": "High",
                "target_platform": "STM32F4 + custom carrier",
            },
            [
                {
                    "name": "STM32F407VGT6",
                    "description": "ARM Cortex-M4 MCU, 1MB Flash.",
                    "quantity": 30,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 7.80,
                    "tax_percent": 5,
                    "vendor": "Mouser",
                    "category": "Microcontrollers",
                    "link": "https://www.mouser.com/ProductDetail/STMicroelectronics/STM32F407VGT6",
                    "notes": "Main MCU for embedded control.",
                    "data": {
                        "mfr": "STMicroelectronics",
                        "mpn": "STM32F407VGT6",
                        "supplier_sku": "511-STM32F407VGT6",
                        "lead_time": "6 weeks",
                        "notes": "Needs 8MHz crystal.",
                        "package": "LQFP-100",
                        "temp_grade": "-40 to 85C",
                    },
                },
                {
                    "name": "LP5907MFX-3.3/NOPB",
                    "description": "250mA, low-noise LDO.",
                    "quantity": 50,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 0.85,
                    "tax_percent": 5,
                    "vendor": "Digi-Key",
                    "category": "Power",
                    "link": "https://www.digikey.com/en/products/detail/texas-instruments/LP5907MFX-3-3-NOPB/1887367",
                    "notes": "3.3V rail for MCU.",
                    "data": {
                        "mfr": "Texas Instruments",
                        "mpn": "LP5907MFX-3.3/NOPB",
                        "supplier_sku": "296-17746-1-ND",
                        "lead_time": "2-3 weeks",
                        "notes": "Use 1uF input/output cap.",
                        "package": "SOT-23-5",
                        "temp_grade": "-40 to 125C",
                    },
                },
            ],
        )
    if kind == "iot":
        return (
            {
                "needed_by": "2026-03-01",
                "department": "IoT",
                "budget_code": "IOT-GW-2026",
                "priority": "Medium",
                "connectivity": "Wi-Fi + LTE fallback",
            },
            [
                {
                    "name": "ESP32-WROOM-32E",
                    "description": "Wi-Fi + BLE module.",
                    "quantity": 40,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 3.95,
                    "tax_percent": 5,
                    "vendor": "Digi-Key",
                    "category": "Modules",
                    "link": "https://www.digikey.com/en/products/detail/espressif-systems/ESP32-WROOM-32E/10259308",
                    "notes": "Primary Wi-Fi module.",
                    "data": {
                        "mfr": "Espressif Systems",
                        "mpn": "ESP32-WROOM-32E",
                        "supplier_sku": "1965-ESP32-WROOM-32E-ND",
                        "lead_time": "3-4 weeks",
                        "notes": "Add external antenna option.",
                        "certs": "FCC, CE, IC",
                    },
                },
                {
                    "name": "Quectel BG95-M3",
                    "description": "LTE Cat-M1/NB-IoT module.",
                    "quantity": 25,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 13.80,
                    "tax_percent": 5,
                    "vendor": "Mouser",
                    "category": "Cellular Modules",
                    "link": "https://www.mouser.com/ProductDetail/Quectel/BG95-M3",
                    "notes": "LTE fallback and telemetry.",
                    "data": {
                        "mfr": "Quectel",
                        "mpn": "BG95-M3",
                        "supplier_sku": "855-BG95-M3",
                        "lead_time": "6-8 weeks",
                        "notes": "Needs LTE antenna and SIM.",
                        "certs": "FCC, PTCRB",
                    },
                },
            ],
        )
    if kind == "network":
        return (
            {
                "needed_by": "2026-02-10",
                "department": "IT",
                "budget_code": "IT-NET-2026",
                "priority": "Medium",
                "network_type": "Enterprise LAN refresh",
            },
            [
                {
                    "name": "UniFi Switch 24 PoE",
                    "description": "24-port PoE switch for lab rack.",
                    "quantity": 1,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 379.00,
                    "tax_percent": 5,
                    "vendor": "CDW",
                    "category": "Networking",
                    "link": "https://store.ui.com/us/en/products/usw-24-poe",
                    "notes": "Replace aging switch in lab.",
                    "data": {
                        "mfr": "Ubiquiti",
                        "mpn": "USW-24-POE",
                        "supplier_sku": "USW-24-POE",
                        "lead_time": "2-4 weeks",
                        "notes": "PoE for access points.",
                        "speed": "1 Gbps",
                    },
                },
                {
                    "name": "Cisco SFP-10G-SR",
                    "description": "10GBASE-SR SFP+ transceiver.",
                    "quantity": 4,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 189.00,
                    "tax_percent": 5,
                    "vendor": "CDW",
                    "category": "Networking",
                    "link": "https://www.cisco.com/c/en/us/products/collateral/interfaces-modules/transceiver-modules/data_sheet_c78-455693.html",
                    "notes": "For short-range fiber uplinks.",
                    "data": {
                        "mfr": "Cisco",
                        "mpn": "SFP-10G-SR",
                        "supplier_sku": "SFP-10G-SR",
                        "lead_time": "2-3 weeks",
                        "notes": "OM3 fiber compatible.",
                        "speed": "10 Gbps",
                    },
                },
            ],
        )
    if kind == "amazon":
        return (
            {
                "needed_by": "2026-02-05",
                "department": "Operations",
                "budget_code": "OPS-AMZ-2026",
                "priority": "Low",
                "po_ref": "AMZ-PO-1042",
            },
            [
                {
                    "name": "Samsung 970 EVO Plus 1TB NVMe SSD",
                    "description": "M.2 NVMe SSD for test rigs.",
                    "quantity": 3,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 79.99,
                    "tax_percent": 5,
                    "vendor": "Amazon",
                    "category": "Storage",
                    "link": "https://www.amazon.com/dp/B07MFZY2F2",
                    "notes": "For imaging stations.",
                    "data": {
                        "asin": "B07MFZY2F2",
                        "link": "https://www.amazon.com/dp/B07MFZY2F2",
                        "notes": "NVMe SSD for test rigs.",
                    },
                },
                {
                    "name": "Anker 8-in-1 USB-C Hub",
                    "description": "USB-C hub with HDMI and Ethernet.",
                    "quantity": 5,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 49.99,
                    "tax_percent": 5,
                    "vendor": "Amazon",
                    "category": "Accessories",
                    "link": "https://www.amazon.com/dp/B07ZVKTP53",
                    "notes": "For laptop docking.",
                    "data": {
                        "asin": "B07ZVKTP53",
                        "link": "https://www.amazon.com/dp/B07ZVKTP53",
                        "notes": "USB-C hub for dev laptops.",
                    },
                },
            ],
        )
    if kind == "digikey":
        return (
            {
                "needed_by": "2026-02-12",
                "department": "Engineering",
                "budget_code": "ENG-COMP-2026",
                "priority": "High",
                "po_ref": "DK-PO-3381",
            },
            [
                {
                    "name": "ATmega328P-AU",
                    "description": "8-bit AVR MCU, 32KB Flash.",
                    "quantity": 25,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 2.65,
                    "tax_percent": 5,
                    "vendor": "Digi-Key",
                    "category": "Microcontrollers",
                    "link": "https://www.digikey.com/en/products/detail/microchip-technology/ATMEGA328P-AU/1914589",
                    "notes": "For legacy controller builds.",
                    "data": {
                        "mfr": "Microchip",
                        "mpn": "ATMEGA328P-AU",
                        "supplier_sku": "ATMEGA328P-AU-ND",
                        "lead_time": "3-4 weeks",
                        "notes": "Use 16MHz crystal.",
                        "digikey_part_number": "ATMEGA328P-AU-ND",
                        "link": "https://www.digikey.com/en/products/detail/microchip-technology/ATMEGA328P-AU/1914589",
                    },
                },
                {
                    "name": "BSS138 MOSFET",
                    "description": "N-channel MOSFET for level shifting.",
                    "quantity": 100,
                    "unit": "pcs",
                    "currency": "USD",
                    "unit_price": 0.28,
                    "tax_percent": 5,
                    "vendor": "Digi-Key",
                    "category": "Discrete",
                    "link": "https://www.digikey.com/en/products/detail/infineon-technologies/BSS138CT-ND/1965615",
                    "notes": "Use for I2C level shifting.",
                    "data": {
                        "mfr": "Infineon",
                        "mpn": "BSS138",
                        "supplier_sku": "BSS138CT-ND",
                        "lead_time": "2-3 weeks",
                        "notes": "SOT-23 package.",
                        "digikey_part_number": "BSS138CT-ND",
                        "link": "https://www.digikey.com/en/products/detail/infineon-technologies/BSS138CT-ND/1965615",
                    },
                },
            ],
        )
    return ({}, [])


def _template_schema(*, kind: str) -> dict:
    common_bom_fields = [
        {"key": "needed_by", "label": "Needed By", "type": "date"},
        {"key": "department", "label": "Department", "type": "text"},
        {"key": "budget_code", "label": "Budget Code", "type": "text"},
        {"key": "priority", "label": "Priority", "type": "select", "options": ["Low", "Medium", "High"]},
    ]
    common_item_fields = [
        {"key": "mfr", "label": "Manufacturer", "type": "text"},
        {"key": "mpn", "label": "MPN", "type": "text"},
        {"key": "supplier_sku", "label": "Supplier SKU", "type": "text"},
        {"key": "lead_time", "label": "Lead Time", "type": "text"},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]

    if kind == "quick":
        bom_fields = [{"key": "purpose", "label": "Purpose", "type": "textarea"}]
        item_fields = [{"key": "link", "label": "Link", "type": "url"}]
    elif kind == "mid":
        bom_fields = [{"key": "purpose", "label": "Purpose", "type": "textarea"}]
        item_fields = common_item_fields + [{"key": "link", "label": "Link", "type": "url"}]
    elif kind == "large":
        bom_fields = common_bom_fields + [{"key": "purpose", "label": "Purpose", "type": "textarea"}]
        item_fields = common_item_fields + [
            {"key": "datasheet", "label": "Datasheet URL", "type": "url"},
            {"key": "alt_part", "label": "Alternate Part", "type": "text"},
        ]
    elif kind == "embedded":
        bom_fields = common_bom_fields + [{"key": "target_platform", "label": "Target Platform", "type": "text"}]
        item_fields = common_item_fields + [
            {"key": "package", "label": "Package", "type": "text"},
            {"key": "temp_grade", "label": "Temp Grade", "type": "text"},
        ]
    elif kind == "iot":
        bom_fields = common_bom_fields + [{"key": "connectivity", "label": "Connectivity", "type": "text"}]
        item_fields = common_item_fields + [{"key": "certs", "label": "Certifications", "type": "text"}]
    elif kind == "network":
        bom_fields = common_bom_fields + [{"key": "network_type", "label": "Network Type", "type": "text"}]
        item_fields = common_item_fields + [{"key": "speed", "label": "Speed", "type": "text"}]
    elif kind == "amazon":
        bom_fields = common_bom_fields + [{"key": "po_ref", "label": "PO Ref", "type": "text"}]
        item_fields = [
            {"key": "asin", "label": "ASIN", "type": "text"},
            {"key": "link", "label": "Link", "type": "url"},
            {"key": "notes", "label": "Notes", "type": "textarea"},
        ]
    elif kind == "digikey":
        bom_fields = common_bom_fields + [{"key": "po_ref", "label": "PO Ref", "type": "text"}]
        item_fields = common_item_fields + [
            {"key": "digikey_part_number", "label": "Digi-Key Part Number", "type": "text"},
            {"key": "link", "label": "Link", "type": "url"},
        ]
    else:
        bom_fields = common_bom_fields
        item_fields = common_item_fields

    sample_bom, sample_items = _sample_data(kind)
    return {
        "version": 1,
        "bom_fields": bom_fields,
        "item_fields": item_fields,
        "sample_bom": sample_bom,
        "sample_items": sample_items,
    }


class Command(BaseCommand):
    help = "Seed global BOM templates (idempotent)."

    def handle(self, *args, **options):
        templates = [
            ("Quick Purchase", "A minimal purchase request template.", "quick"),
            ("Mid Purchase", "A balanced template for typical purchases.", "mid"),
            ("Large Purchase", "A detailed template for larger purchases.", "large"),
            ("Embedded", "Template for embedded electronics procurement.", "embedded"),
            ("IoT", "Template for IoT hardware procurement.", "iot"),
            ("Network", "Template for networking equipment procurement.", "network"),
            ("Amazon", "Template for Amazon purchases.", "amazon"),
            ("Digi-Key", "Template for Digi-Key component purchases.", "digikey"),
        ]

        created = 0
        updated = 0
        for name, description, kind in templates:
            obj, was_created = BomTemplate.objects.update_or_create(
                owner=None,
                name=name,
                defaults={"description": description, "schema": _template_schema(kind=kind)},
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        self.stdout.write(self.style.SUCCESS(f"Seeded templates: created={created} updated={updated}"))
