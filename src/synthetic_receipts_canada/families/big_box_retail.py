"""Sales receipt from a large office-supply and electronics chain in Québec.

Structure observed on a real 2026 receipt (see docs/templates/big-box-retail.md); every name
and number here is fictitious. Traps for an extractor: the item price uses a decimal point
with the tax code glued on ('49.99B') while totals use a comma, 'Total partiel' comes before
'Total', the GST number is printed without its RT0001 suffix, and many digit runs carry no
label (transaction groups, associate, UPC, SKU, barcode digits).
"""

import random
import textwrap
from datetime import datetime

from .. import REPO_URL, SCHEMA_VERSION
from ..fakes import CITIES, POSTAL_LETTERS, fake_gst_number, fake_postal_code, fake_qst_number, random_day
from ..layout import Align, Receipt
from ..money import cash_rounded, gst_cents, qst_cents
from ..render import PAPER

BANNERS = ["BUREAU FICTIF", "FOURNITURES DOH", "ELECTRO SPECIMEN", "PAPETERIE QUIDAM"]
# English-form street names, type last, as the chain prints them even in Québec.
STREET_NAMES = ["La Place-Doh", "Des Fictifs", "Principale", "Du Quidam", "Carrefour-Spécimen"]
STREET_TYPES = ["St", "St", "Blvd", "Ave"]
# (description as abbreviated by the till, low, high in cents, electronic: carries an eco fee)
PRODUCTS = [
    ("Manette sans fil Doh", 4999, 9999, True), ("Clavier sans fil Fictf", 2999, 7999, True),
    ("Souris optique Quidam", 1499, 3999, True), ("Ecouteurs bt Specimen", 2999, 12999, True),
    ("Cle USB 64 Go Doh", 1299, 2999, True), ("Cartouche encre noire", 2499, 5999, False),
    ("Papier 8.5x11 500f", 899, 1499, False), ("Stylos gel 12 pqt", 799, 1699, False),
    ("Cahier spirale 3 suj", 399, 899, False), ("Classeur 1po Fictif", 499, 1299, False),
    ("Chargeur USB-C 30W", 2499, 4999, True), ("Cable HDMI 2m Doh", 1499, 2999, True),
]


def _comma(cents: int) -> str:
    return f"{cents // 100},{cents % 100:02d}"


def _random_datetime(rng: random.Random) -> datetime:
    day = random_day(rng)
    return day.replace(hour=rng.randint(9, 20), minute=rng.randint(0, 59))


def _boxed(r: Receipt, text: str) -> None:
    r.add("*" * r.columns)
    for line in textwrap.wrap(text, r.columns):
        r.add(line, align=Align.CENTER)


def _draw_items(rng: random.Random) -> list[dict]:
    items = []
    for _ in range(rng.randint(1, 5)):
        desc, lo, hi, electronic = rng.choice(PRODUCTS)
        price = rng.randint(lo // 100, hi // 100 - 1) * 100 + rng.choice([99, 99, 49, 97])
        items.append({"kind": "product", "qty": 1, "description": desc,
                      "upc": f"{rng.randint(10**10, 9 * 10**11 - 1):012d}",
                      "sku": f"{rng.randint(100_000, 999_999)}" if electronic else None,
                      "eco_fee_included": electronic,
                      "unit_price_cents": price, "line_total_cents": price, "tax_flags": "B"})
    return items


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    cols = PAPER[paper_mm]["columns"]
    r = Receipt(columns=cols)
    banner = rng.choice(BANNERS)
    city, letter = rng.choice(CITIES)
    street = f"{rng.randint(1, 3999)} {rng.choice(STREET_NAMES)} {rng.choice(STREET_TYPES)}"
    postal = fake_postal_code(rng, letter)
    phone = f"819-555-{rng.randint(100, 199):04d}"
    store = f"{rng.randint(1, 499):04d}"
    when = _random_datetime(rng)
    groups = f"{rng.randint(1, 999):05d} 001 {rng.randint(1, 12):03d}"
    number = f"{rng.randint(10_000, 99_999)}"
    associate = f"{rng.randint(1_000_000, 2_999_999)}"
    gst_number = fake_gst_number(rng)
    qst_number = fake_qst_number(rng) + rng.choice(POSTAL_LETTERS) + rng.choice(POSTAL_LETTERS)
    survey = "".join(rng.choice(POSTAL_LETTERS) for _ in range(3)) + store.lstrip("0")
    domain = banner.lower().replace(" ", "") + ".example"
    prize = rng.choice([250, 500, 1000])

    # Totals of 1000 $ or more were not observed, nor how they would print: 5 items at the
    # top of PRODUCTS stay well under it, and raising those prices must keep it so.
    items = _draw_items(rng)
    subtotal = sum(i["line_total_cents"] for i in items)
    gst, qst = gst_cents(subtotal), qst_cents(subtotal)
    total = subtotal + gst + qst
    assert total < 100_000
    # Cash pays the total rounded to 5 cents; the receipt keeps the cents and prints no rounding line.
    rounded = cash_rounded(total)
    ceilings = sorted({-(-rounded // step) * step for step in (500, 1000, 2000, 5000, 10000)})
    cash = rounded if rng.random() < 0.2 else rng.choice(ceilings[:3])
    change = cash - rounded

    r.add(banner, align=Align.CENTER)
    r.add(city, align=Align.CENTER)
    r.add(street, align=Align.CENTER)
    r.add(f"{city}, QC {postal}", align=Align.CENTER)
    r.add(phone, align=Align.CENTER)
    r.two_columns("VENTE", f"{groups} {number}")
    r.add(f"{store} {when:%d/%m/%y %H:%M}", align=Align.RIGHT)
    r.add()
    r.add(associate)
    r.add()
    for item in items:
        r.add(f"{item['qty']:<5}{item['description']}")
        price = f"{item['line_total_cents'] // 100}.{item['line_total_cents'] % 100:02d}{item['tax_flags']}"
        r.two_columns(f"     {item['upc']}", price)
        if item["sku"]:
            r.add(f"     UGS {item['sku']} d'écofrais inclus")
    r.two_columns("Total partiel", _comma(subtotal))
    r.two_columns("     5.00% TPS", _comma(gst))
    r.two_columns("     9.975% TVQ", _comma(qst))
    r.add()
    r.two_columns("Total", f"{_comma(total)} $")
    r.two_columns("Comptant", _comma(cash))
    r.two_columns("Comptant Rendu", _comma(change))
    notices = rng.random() < 0.8
    if notices:
        _boxed(r, "Les écouteurs et casques ouverts ne peuvent pas être retournés.")
        _boxed(r, f"Échangez votre ancien appareil contre une carte-cadeau {banner}. "
                  "Demandez à un associé pour plus de détails.")
        r.add("*" * cols)
    r.add()
    r.add(f"Merci d'avoir magasiné chez {banner}", align=Align.CENTER)
    r.add()
    r.add(f"TPS : {gst_number[:9]} - TVQ : {qst_number}")
    r.add()
    r.add()
    for line in textwrap.wrap(f"Partagez vos commentaires et courez la chance de gagner une "
                              f"carte-cadeau {banner} de {prize} $.", cols):
        r.add(line, align=Align.CENTER)
    r.add()
    r.qr(REPO_URL)
    r.add()
    r.add("Scannez le code QR, textez", align=Align.CENTER)
    r.add(f"{survey} au 12345,", align=Align.CENTER)
    r.add(f"ou visitez {domain}/survey/{store.lstrip('0')}", align=Align.CENTER)
    for line in textwrap.wrap("Les frais standards de messagerie et de données s'appliquent.", cols):
        r.add(line, align=Align.CENTER)
    r.add("Pour connaître les règlements", align=Align.CENTER)
    r.add("du concours,", align=Align.CENTER)
    r.add(f"consultez le site aide.{domain}", align=Align.CENTER)
    r.add()
    code = f"{store}{when:%d%m%y}{number}{groups[-2:]}"
    r.barcode(code)
    r.add(" ".join(code), align=Align.CENTER)
    r.add()
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)

    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "big_box_retail",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": banner, "address_lines": [street, f"{city}, QC {postal}"], "phone": phone},
        "store_number": store,
        "datetime": when.isoformat(),
        "transaction_number": number,
        "associate_id": associate,
        "items": items,
        "subtotal_cents": subtotal,
        "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "cents": gst},
                  {"kind": "QST", "label": "TVQ", "rate": "0.09975", "cents": qst}],
        "total_cents": total,
        "tip_cents": None,
        "gst_number": gst_number[:9],
        "qst_number": qst_number,
        "payment_method": "cash",
        "tenders": [{"method": "cash", "cents": cash}],
        "cash_rounding_cents": rounded - total,
        "change_cents": change,
        "card": None,
        "document_kind": "sales_receipt",
        "text_lines": r.text_lines(),
    }
    return r, truth
