"""Veterinary clinic invoice printed on a thermal ticket in Québec.

Structure observed on a real 2026 invoice (see docs/templates/professional-invoice.md); every
name and number here is fictitious, and client names use the placeholder surnames of fakes.py.
Unlike a store receipt it names a client (with a file number) and a patient, and prints no
time. Traps for an extractor: the date is '7-nov.-2026', weight ranges in point decimals sit
inside descriptions, the GST/QST numbers carry no suffix, and 'Monnaie' and 'Solde' follow
the total without being payments.
"""

import random
import textwrap
from datetime import date, timedelta

from .. import SCHEMA_VERSION
from ..fakes import CITIES, STREETS, fake_full_name, fake_gst_number, fake_postal_code, fake_qst_number
from ..layout import Align, Receipt, Size
from ..money import gst_cents, qst_cents
from ..render import PAPER

CLINIC_NAMES = ["Doh", "du Quidam", "Fictive", "Spécimen", "des Fictifs"]
# Only 'sept.' was observed; the others are the usual French abbreviations.
MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
PET_NAMES = ["Biscuit", "Moka", "Filou", "Caramel", "Pacha", "Nala", "Galette", "Pistache", "Praline", "Rocco"]
# (dog, cat) weight bands for parasite treatments, printed '10.1 kg à 20kg'
WEIGHT_BANDS = {"canin": [(2, 5), (5, 10), (10, 20), (20, 40), (40, 60)], "félin": [(2, 4), (4, 8)]}


def _comma(cents: int) -> str:
    return f"{cents // 100},{cents % 100:02d} $"


def _draw_items(rng: random.Random, species: str) -> list[dict]:
    items = []
    for _ in range(rng.randint(1, 4)):
        kind = rng.choice(["exam", "vaccine", "drug", "drug", "food"])
        if kind == "exam":
            desc, lo, hi = "Examen de santé complet", 7000, 9500
        elif kind == "vaccine":
            desc, lo, hi = f"Vaccin annuel {'DHPP' if species == 'canin' else 'RCP'}", 3500, 5500
        elif kind == "drug":
            low, high = rng.choice(WEIGHT_BANDS[species])
            desc, lo, hi = f"Antiparasitaire DOH {species} {low}.1 kg à {high}kg", 2500, 6500
        else:
            desc, lo, hi = f"Nourriture {species} FICTIVE {rng.choice([2, 4, 8])} kg", 3000, 9000
        price = rng.randint(lo, hi)
        items.append({"kind": "service" if kind == "exam" else "product", "qty": 1, "description": desc,
                      "unit_price_cents": price, "line_total_cents": price, "tax_flags": None})
    return items


def _right_block(r: Receipt, label: str, amount: str) -> None:
    r.add(f"{label:<13}{amount:>10}".rjust(r.columns))


def _date(d: date) -> str:
    return f"{d.day}-{MONTHS[d.month - 1]}-{d.year}"


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    cols = PAPER[paper_mm]["columns"]
    r = Receipt(columns=cols)
    clinic = rng.choice(CLINIC_NAMES)
    city, letter = rng.choice(CITIES)
    street = f"{rng.randint(10, 3999)} {rng.choice(STREETS)}"
    postal = fake_postal_code(rng, letter)
    phone = f"(819)555-{rng.randint(100, 199):04d}"
    gst_number = fake_gst_number(rng)[:9]
    qst_number = fake_qst_number(rng)[:10]
    number = f"{rng.randint(100_000, 699_999)}"
    # A dated invoice naming a client is the most personal document here: keep its dates out
    # of the year the source invoice was printed, so no sample can echo a real visit.
    day = date(2024, 1, 1) + timedelta(days=rng.randint(0, 365 * 2))
    civility = rng.choice(["M.", "Mme"])
    client = fake_full_name(rng)
    client_id = f"{rng.randint(1_000, 29_999)}"
    client_city, client_letter = rng.choice(CITIES)
    client_street = f"{rng.randint(10, 3999)} {rng.choice(STREETS)}"
    client_postal = fake_postal_code(rng, client_letter)
    species = rng.choice(["canin", "canin", "félin"])
    pet = rng.choice(PET_NAMES)
    pet_id = f"{rng.randint(10_000, 49_999)}"

    # Only cash with a total already a multiple of 5 cents was observed: no rounding line.
    while True:
        items = _draw_items(rng, species)
        subtotal = sum(i["line_total_cents"] for i in items)
        gst, qst = gst_cents(subtotal), qst_cents(subtotal)
        total = subtotal + gst + qst
        if total % 5 == 0:
            break
    ceilings = sorted({-(-total // step) * step for step in (500, 1000, 2000, 5000, 10000)})
    cash = total if rng.random() < 0.2 else rng.choice(ceilings[:3])
    change = cash - total

    for line in ("Clinique", "vétérinaire", f"{clinic} inc"):
        r.add(line, align=Align.CENTER, size=Size.DOUBLE)
    r.add(street)
    r.add(f"{city}, QC {postal}")
    r.add(f"Téléphone:  {phone}")
    r.add(f"TPS: {gst_number}  TVQ: {qst_number}")
    r.add()
    r.add(f"Facture: {number}")
    r.add(f"Date: {_date(day)}")
    r.add()
    r.add(f"{civility} {client} ({client_id})")
    r.add(client_street)
    r.add(f"{client_city}, QC  {client_postal}")
    r.add()
    r.add()
    r.add(f"{pet} - {pet_id}")
    for item in items:
        price = _comma(item["line_total_cents"])
        head = f"   {item['qty']} "
        parts = textwrap.wrap(item["description"], cols - len(head) - len(price) - 2)
        r.add(f"{head}{parts[0]}".ljust(cols - len(price)) + price)
        for part in parts[1:]:
            r.add(" " * len(head) + part)
    r.add()
    _right_block(r, "Sous-total:", _comma(subtotal))
    _right_block(r, "TPS(5%):", _comma(gst))
    _right_block(r, "TVQ(9,975%):", _comma(qst))
    _right_block(r, "Total:", _comma(total))
    r.add()
    r.add(f"{_date(day)}  {'Comptant:':<11}{_comma(cash):>10}".rjust(cols))
    r.add()
    r.add(f"{'  Monnaie':<13}{_comma(change):>10}".rjust(cols))
    _right_block(r, "Solde:", _comma(0))
    notices = rng.random() < 0.8
    if notices:
        r.add()
        for line in textwrap.wrap("AUCUN RETOUR SUR LES MEDICAMENTS POUR DES RAISONS DE SÉCURITÉ <------------", cols):
            r.add(line)
        r.add()
        for line in textwrap.wrap("Les frais de prescription et de préparation sont inclus dans le prix "
                                  "total des médicaments", cols):
            r.add(line)
        r.add()
        for line in textwrap.wrap("Des intérêts de 2% par mois équivalent à un taux de 24% annuellement "
                                  "seront appliqués sur tout solde impayé", cols):
            r.add(line)
    r.add()
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)

    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "professional_invoice",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": f"Clinique vétérinaire {clinic} inc",
                     "address_lines": [street, f"{city}, QC {postal}"], "phone": phone},
        "store_number": None,
        "datetime": day.isoformat(),
        "transaction_number": number,
        "client": {"name": f"{civility} {client}", "id": client_id,
                   "address_lines": [client_street, f"{client_city}, QC  {client_postal}"]},
        "patient": {"name": pet, "id": pet_id, "species": species},
        "items": items,
        "subtotal_cents": subtotal,
        "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "cents": gst},
                  {"kind": "QST", "label": "TVQ", "rate": "0.09975", "cents": qst}],
        "total_cents": total,
        "tip_cents": None,
        "gst_number": gst_number,
        "qst_number": qst_number,
        "payment_method": "cash",
        "tenders": [{"method": "cash", "cents": cash}],
        "change_cents": change,
        "balance_cents": 0,
        "card": None,
        "document_kind": "invoice",
        "text_lines": r.text_lines(),
    }
    return r, truth
