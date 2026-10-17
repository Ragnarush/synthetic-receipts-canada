"""Card terminal slip printed as a ticket of its own, apart from any sales receipt.

Structure observed on real 2026 tickets (see docs/templates/payment-terminal-slip.md); every
name and number here is fictitious. Two variants: 'store_header', where the till prints the
store header then the 'RELEVE DE TRANSACTION' slip (alcohol crown store), and
'standalone_terminal', where a terminal with no till attached prints everything itself
(convenience store). Neither carries items, taxes or a purchase total. In a split payment
MONTANT is only the debit share, so the ground truth always leaves total_cents null.
"""

import random
import textwrap
from datetime import timedelta

from .. import SCHEMA_VERSION
from ..fakes import AREA_CODES, CITIES, STREETS, fake_postal_code
from ..layout import Align, Receipt, Size, ascii_upper
from ..render import PAPER
from . import _terminal
from ._crown_store import ALCOHOL, ALCOHOL_BANNERS, alcohol_header, random_datetime, reprint_banner, shelf_price

SHOP_PREFIXES = ["DEP", "DEP GEN", "DEPANNEUR", "MARCHE", "DEP ET VIDEO"]
SHOP_NAMES = ["DOH", "FICTIF", "QUIDAM", "SPECIMEN", "UNTEL", "DU COIN DOH", "LE FICTIF"]
SHOP_SUFFIXES = ["", "", "ENR", "INC", "ST-DOH", "S.QUI"]
STANDALONE_PAPER_MM = 58  # the terminal prints on its own narrow roll, whatever the store uses


def _base_truth(paper_mm: int, variant: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "family": "payment_terminal_slip",
        "variant": variant,
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "items": [],
        "taxes_included": None,
        "subtotal_cents": None,
        "taxes": [],
        "total_cents": None,
        "tip_cents": None,
        "gst_number": None,
        "qst_number": None,
        "payment_method": "debit",
        "change_cents": None,
        "document_kind": "payment_slip",
    }


def _store_header(rng: random.Random, paper_mm: int) -> tuple[Receipt, dict]:
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

    return r, {
        **_base_truth(paper_mm, "store_header"),
        "merchant": {"name": banner,
                     "address_lines": [f"{street} - {city}", f"{city}, QC {postal}"],
                     "phone": phone},
        "store_number": store,
        "datetime": when.replace(second=0).isoformat(),
        "transaction_number": number,
        "tenders": [{"method": "debit", "cents": debit}],
        "card": card,
        "reprint": reprint,
    }


def _standalone_terminal(rng: random.Random) -> tuple[Receipt, dict]:
    r = Receipt(columns=PAPER[STANDALONE_PAPER_MM]["columns"])
    name = " ".join(p for p in (rng.choice(SHOP_PREFIXES), rng.choice(SHOP_NAMES), rng.choice(SHOP_SUFFIXES)) if p)
    city, letter = rng.choice(CITIES)
    street = ascii_upper(f"{rng.randint(10, 3999)} {rng.choice(STREETS)}")
    # The merchant block is set at the terminal and often wraps at a word well before the edge.
    address_lines = textwrap.wrap(street, rng.choice([18, 22, r.columns]))
    locality = f"{ascii_upper(city)}, QC {fake_postal_code(rng, letter).replace(' ', '')}"
    phone = f"{rng.choice(AREA_CODES)}555{rng.randint(100, 199):04d}"
    when = random_datetime(rng) + timedelta(seconds=rng.randint(0, 59))
    cents = rng.randint(150, 4500)
    merchant_id = f"{rng.randint(1_000_000, 9_999_999)}"
    terminal_id = f"{rng.randint(1, 4):03d}"
    batch = f"{rng.randint(1, 999):03d}001"
    reference = f"{rng.randint(1, 999):08d}"
    auth = "".join(rng.choice("0123456789ABCDEF") for _ in range(6))
    trace = f"{rng.randint(1, 999_999):08d}"
    last4 = f"{rng.randint(0, 9999):04d}"

    for line in [name, *address_lines, locality, phone]:
        r.add(line, align=Align.CENTER, bold=True)
    r.add()
    r.add("VENTE DEBIT", align=Align.CENTER, bold=True, size=Size.DOUBLE)
    r.add()
    r.add(f"IDM: {merchant_id}", bold=True)
    r.two_columns(f"IDT: {terminal_id}", f"No. REF: {reference}", bold=True)
    r.two_columns(f"No Lot: {batch}", f"NRE: {reference}", bold=True)
    r.two_columns(f"{when:%m/%d/%y}", f"{when:%H:%M:%S}", bold=True)
    r.add(f"CODE APPR: {auth}", bold=True)
    r.add(f"No Trace: {trace}", bold=True)
    r.two_columns("DEBIT/PAR DEFAUT", "Sans Contact", bold=True)
    r.add(f"{'*' * 12}{last4}", bold=True)
    r.add()
    r.two_columns("MONTANT", f"${cents // 100}.{cents % 100:02d}", bold=True, size=Size.DOUBLE)
    r.add()
    r.add("APPROUVE", align=Align.CENTER, bold=True)
    r.add()
    r.add("Interac", bold=True)
    r.add(f"AID: {_terminal.INTERAC_AID}", bold=True)
    r.add("TVR: 80 00 00 80 00", bold=True)
    r.add()
    for line in ["VOTRE COMPTE SERA DEBITE DU", "MONTANT CI-DESSUS",
                 "VEUILLEZ CONSERVER CETTE COPIE", "POUR LA VERIFICATION DU RELEVE"]:
        r.add(line, align=Align.CENTER)
    r.add()
    r.add("THANK YOU! / MERCI!", align=Align.CENTER, bold=True)
    r.add()
    r.add("COPIE CLIENT", align=Align.CENTER, bold=True)
    r.add()
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)
    r.wrap_overflow()

    return r, {
        **_base_truth(STANDALONE_PAPER_MM, "standalone_terminal"),
        "merchant": {"name": name, "address_lines": [*address_lines, locality], "phone": phone},
        "store_number": None,
        "datetime": when.isoformat(),
        "transaction_number": None,
        "tenders": [{"method": "debit", "cents": cents}],
        "card": {"network": "Interac", "masked_number": f"{'*' * 12}{last4}",
                 "account": "DEBIT/PAR DEFAUT", "entry": "Sans Contact",
                 "datetime": when.isoformat(), "reference": reference, "authorization": auth,
                 "merchant_id": merchant_id, "terminal_id": terminal_id, "batch": batch, "trace": trace},
        "reprint": False,
    }


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    r, truth = _store_header(rng, paper_mm) if rng.random() < 0.5 else _standalone_terminal(rng)
    truth["text_lines"] = r.text_lines()
    return r, truth
