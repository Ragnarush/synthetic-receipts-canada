"""Card terminal slip printed as a ticket of its own, apart from the sales receipt.

Structure observed on real 2026 tickets of a Québec alcohol crown store (see
docs/templates/payment-terminal-slip.md); every name and number here is fictitious. The ticket
carries the store header and the 'RELEVE DE TRANSACTION' slip, nothing else: no items, no
taxes, no purchase total. In a split payment MONTANT is only the debit share, so the ground
truth leaves total_cents null.
"""

import random

from .. import SCHEMA_VERSION
from ..fakes import CITIES, STREETS, fake_postal_code
from ..layout import Align, Receipt
from ..render import PAPER
from . import _terminal
from ._crown_store import ALCOHOL, ALCOHOL_BANNERS, alcohol_header, random_datetime, reprint_banner, shelf_price


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    r = Receipt(columns=PAPER[paper_mm]["columns"])
    banner = rng.choice(ALCOHOL_BANNERS)
    city, letter = rng.choice(CITIES)
    street = f"{rng.randint(10, 3999)}, {rng.choice(STREETS)}"
    postal = fake_postal_code(rng, letter)
    phone = f"819-555-{rng.randint(100, 199):04d}"
    when = random_datetime(rng)
    number = f"{rng.randint(10_000, 199_999)}"
    store = f"{rng.randint(10_000, 99_999)}"
    register = rng.randint(1, 4)
    cashier = f"{rng.randint(100_000, 2_999_999)}"
    reprint = rng.random() < 0.2

    sale = 0
    for _ in range(rng.randint(1, 3)):
        _, lo, hi = rng.choice(ALCOHOL)
        sale += shelf_price(rng, lo, hi, False)
    split = rng.random() < 0.35
    # In a split payment the cash part is a round amount and only the rest goes through the terminal.
    debit = sale - rng.randrange(1000, max(1100, sale - 500), 1000) if split else sale

    alcohol_header(r, banner, street, city, postal, phone, number, store, register, cashier, when)
    r.add()
    if reprint:
        reprint_banner(r)
    r.add()
    card = _terminal.releve_slip(r, rng, debit, when, number)
    r.add()
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)

    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "payment_terminal_slip",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": banner,
                     "address_lines": [f"{street} - {city}", f"{city}, QC {postal}"],
                     "phone": phone},
        "store_number": store,
        "datetime": when.replace(second=0).isoformat(),
        "transaction_number": number,
        "items": [],
        "taxes_included": None,
        "subtotal_cents": None,
        "taxes": [],
        "total_cents": None,
        "tip_cents": None,
        "gst_number": None,
        "qst_number": None,
        "payment_method": "debit",
        "tenders": [{"method": "debit", "cents": debit}],
        "change_cents": None,
        "card": card,
        "reprint": reprint,
        "document_kind": "payment_slip",
        "text_lines": r.text_lines(),
    }
    return r, truth
