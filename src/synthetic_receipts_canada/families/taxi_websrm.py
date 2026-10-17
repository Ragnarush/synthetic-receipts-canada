"""Québec taxi receipt from a certified sales recording system (mandatory since 2026-01-01).

Same prescribed blocks as the restaurant family; the differences come from the official taxi
sample: the fare printed large under the name, a single 'Tarif taxi.' line, and the regulatory
levy ('redevance') shown as information, already included in the fare.
"""

import random
from datetime import date, timedelta

from .. import SCHEMA_VERSION
from ..fakes import fake_gst_number, fake_qst_number
from ..layout import Align, Receipt, Size
from ..money import format_cad_fr, gst_cents, qst_cents
from ..render import PAPER
from . import _websrm

TAXI_NAMES = ["Taxi Fictif", "Taxis du Nord Doh", "Coop Taxi Exemple", "Taxi Jean Doh inc.", "Taxi Spécimen"]
HOURS = [(0, 24)]
SECOND_GEN_SEV_MANDATORY = date(2026, 1, 1)  # taxi receipts take this form from this day


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    r = Receipt(columns=PAPER[paper_mm]["columns"])
    name = rng.choice(TAXI_NAMES)
    gst_number, qst_number = fake_gst_number(rng), fake_qst_number(rng)
    when = _websrm.random_datetime(rng, HOURS, SECOND_GEN_SEV_MANDATORY)
    number = f"{rng.randint(1, 999999):06d}"
    fare = rng.randrange(800, 9500, 5)
    levy = 90  # the per-trip levy printed on the official sample
    gst, qst = gst_cents(fare), qst_cents(fare)
    total = fare + gst + qst
    tip = (total * rng.choice([10, 15, 20]) + 50) // 100 if rng.random() < 0.4 else None
    payment = rng.choice(list(_websrm.PAYMENT_METHODS))
    items = [{"qty": 1, "description": "Tarif taxi.", "unit_price_cents": fare,
              "line_total_cents": fare, "tax_flags": "FP"}]

    r.add(name, align=Align.CENTER, bold=True, size=Size.DOUBLE)
    r.add(format_cad_fr(total), align=Align.CENTER, size=Size.DOUBLE)
    r.add()
    _websrm.transaction_lines(r, when, number)
    _websrm.item_line(r, 1, "Tarif taxi.", fare, "FP")
    r.add(f"   redevance@{format_cad_fr(levy)}")
    r.add()
    r.two_columns(" SOUS-TOTAL", format_cad_fr(fare), bold=True)
    r.add()
    _websrm.registration_lines(r, gst_number, qst_number)
    r.add(_websrm.PAYMENT_METHODS[payment], align=Align.CENTER)
    r.add()
    r.add(rng.choice(_websrm.THANKS), align=Align.CENTER)
    r.separator("=")
    _websrm.amount_block(r, gst, qst, total, tip, narrow=True)
    ids = _websrm.websrm_ids(rng)
    processed_at = when + timedelta(seconds=rng.randint(1, 5))
    _websrm.fiscal_footer(r, "PAIEMENT REÇU", ids, processed_at)
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)
    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "taxi_websrm",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": name, "address_lines": [], "phone": None},
        "datetime": when.isoformat(),
        "transaction_number": number,
        "items": items,
        "subtotal_cents": fare,
        "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "cents": gst},
                  {"kind": "QST", "label": "TVQ", "rate": "0.09975", "cents": qst}],
        "total_cents": total,
        "tip_cents": tip,
        "gst_number": gst_number,
        "qst_number": qst_number,
        "payment_method": payment,
        "document_kind": "closing_receipt",
        "websrm": {**ids, "processed_at": processed_at.isoformat()},
        "text_lines": r.text_lines(),
    }
    return r, truth
