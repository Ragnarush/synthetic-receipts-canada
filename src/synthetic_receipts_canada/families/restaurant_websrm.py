"""Québec restaurant / bar receipt printed by a certified sales recording system (WEB-SRM).

Layout follows Revenu Québec's official sample element by element (see _websrm.py). Variation
between generated receipts: merchant, items, alcohol (adds the 'S' flag and the supplementary-tax
note), closing receipt vs original invoice, payment method, tip, server line, column style.
"""

import random
from datetime import timedelta

from .. import SCHEMA_VERSION
from ..fakes import fake_first_name, fake_restaurant
from ..layout import Align, Receipt
from ..money import format_cad_fr, gst_cents, qst_cents
from ..render import PAPER
from . import _websrm

MENU = [
    ("Soupe du jour", 450, 750, "FP"), ("Salade César", 900, 1500, "FP"), ("Poutine", 800, 1400, "FP"),
    ("Club sandwich", 1300, 1900, "FP"), ("Burger maison", 1500, 2200, "FP"), ("Pâtes alfredo", 1600, 2400, "FP"),
    ("Spaghetti", 1200, 1900, "FP"), ("Pizza 12 po", 1700, 2600, "FP"), ("Tartare de saumon", 2200, 3200, "FP"),
    ("Table d'hôte", 2800, 4500, "FP"), ("Menu du jour no 1", 1500, 2100, "FP"), ("Filet de truite", 2400, 3400, "FP"),
    ("Dessert du jour", 600, 1000, "FP"), ("Café", 250, 400, "FP"), ("Thé", 250, 400, "FP"),
    ("Boisson gazeuse", 275, 425, "FP"), ("Eau pétillante", 300, 500, "FP"),
    ("Verre de vin", 900, 1500, "FPS"), ("Bière en fût", 700, 1100, "FPS"), ("Pichet de bière", 1800, 2600, "FPS"),
    ("Cocktail maison", 1100, 1600, "FPS"),
]
HOURS = [(11, 14), (17, 22)]


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    merchant = fake_restaurant(rng)
    r = Receipt(columns=PAPER[paper_mm]["columns"])
    when = _websrm.random_datetime(rng, HOURS)
    number = f"{rng.randint(1, 999999):06d}"
    closing = rng.random() < 0.8  # else an original invoice handed over before payment
    narrow = rng.random() < 0.5

    items = []
    for _ in range(rng.randint(1, 7)):
        name, lo, hi, flags = rng.choice(MENU)
        qty = 1 if rng.random() < 0.8 else rng.randint(2, 4)
        unit = rng.randrange(lo, hi + 1, 25)
        items.append({"qty": qty, "description": name, "unit_price_cents": unit,
                      "line_total_cents": unit * qty, "tax_flags": flags})
    subtotal = sum(i["line_total_cents"] for i in items)
    gst, qst = gst_cents(subtotal), qst_cents(subtotal)
    total = subtotal + gst + qst
    tip = None
    if closing and rng.random() < 0.6:
        tip = (total * rng.choice([10, 15, 18, 20]) + 50) // 100
        tip -= tip % 25 if rng.random() < 0.5 else 0
    payment = rng.choice(list(_websrm.PAYMENT_METHODS)) if closing else None

    _websrm.header(r, merchant.name, merchant.address_lines, merchant.phone, rng)
    _websrm.transaction_lines(r, when, number)
    for item in items:
        _websrm.item_line(r, item["qty"], item["description"], item["line_total_cents"], item["tax_flags"])
    if any("S" in i["tax_flags"] for i in items):
        r.add("   Taxe(s) supplémentaire(s)")
        r.add("   Boiss.alc.(t.incl.)")
    r.two_columns(" SOUS-TOTAL", format_cad_fr(subtotal), bold=True)
    r.add()
    _websrm.registration_lines(r, merchant.gst_number, merchant.qst_number)
    if payment:
        r.add(_websrm.PAYMENT_METHODS[payment], align=Align.CENTER)
        r.add()
    server = fake_first_name(rng) if rng.random() < 0.7 else None
    if server:
        r.add(f"Vous avez été servi par: {server}", align=Align.CENTER)
    if rng.random() < 0.8:
        r.add(rng.choice(_websrm.THANKS), align=Align.CENTER)
    r.separator("=")
    _websrm.amount_block(r, gst, qst, total, tip, narrow)
    ids = _websrm.websrm_ids(rng)
    processed_at = when + timedelta(seconds=rng.randint(1, 5))
    _websrm.fiscal_footer(r, "PAIEMENT REÇU" if closing else "FACTURE ORIGINALE", ids, processed_at)
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)
    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "restaurant_websrm",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": merchant.name, "address_lines": merchant.address_lines, "phone": merchant.phone},
        "datetime": when.isoformat(),
        "transaction_number": number,
        "items": items,
        "subtotal_cents": subtotal,
        "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "cents": gst},
                  {"kind": "QST", "label": "TVQ", "rate": "0.09975", "cents": qst}],
        "total_cents": total,
        "tip_cents": tip,
        "gst_number": merchant.gst_number,
        "qst_number": merchant.qst_number,
        "payment_method": payment,
        "document_kind": "closing_receipt" if closing else "original_invoice",
        "websrm": {**ids, "processed_at": processed_at.isoformat()},
        "text_lines": r.text_lines(),
    }
    return r, truth
