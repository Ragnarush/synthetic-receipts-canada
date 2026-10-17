"""Receipt from a Québec crown corporation store (alcohol or cannabis): prices include taxes.

Structure observed on real 2026 receipts of the two provincial retail monopolies (see
docs/templates/crown-store-tax-included.md); every name and number here is fictitious. The
trap for an extractor: there is no subtotal, the TPS and TVQ lines say '(incl.)' and are
already inside the total, so adding them to it double-counts. Each tax line starts with the
registration number, an amount-looking run of digits.
"""

import random
from fractions import Fraction

from .. import SCHEMA_VERSION
from ..fakes import CITIES, STREETS, _digits_failing_luhn, fake_gst_number, fake_postal_code, fake_qst_number
from ..layout import Align, Receipt, Size
from ..money import round_half_up
from ..render import PAPER
from . import _terminal
from ._crown_store import ALCOHOL, ALCOHOL_BANNERS, alcohol_header, random_datetime, reprint_banner, shelf_price

# Taxes inside a tax-included price P: TPS = P * 5 / 114.975, TVQ = P * 9.975 / 114.975.
GROSS_RATE = Fraction(114975, 100_000)
GST_SHARE = Fraction(5, 100) / GROSS_RATE
QST_SHARE = Fraction(9975, 100_000) / GROSS_RATE

CANNABIS_BANNERS = ["CANNA-DOH", "CANNABIS FICTIF", "CHANVRE SPECIMEN"]
# (description, equivalent grams of dried cannabis per unit, low, high). Federal equivalence:
# 1 g of hash or resin counts as 4 g dried, which is why the printed total weight looks wrong.
CANNABIS = [
    ("3,5g Fleurs séchées Indica Doh", Fraction(7, 2), 2190, 4490),
    ("3,5g Fleurs séchées Sativa Fictive", Fraction(7, 2), 2190, 4490),
    ("3,5g Haschich Spécimen", 14, 3990, 4990),
    ("1g Résine Quidam", 4, 1590, 2490),
    ("3 x 0,5g Préroulés Doh", Fraction(3, 2), 1190, 1990),
    ("28g Fleurs séchées Hybride Doh", 28, 11900, 17900),
]
POSSESSION_LIMIT_G = 30


def _fr(cents: int, space: bool) -> str:
    sign = "(" if cents < 0 else ""
    cents = abs(cents)
    body = f"{cents // 100},{cents % 100:02d}"
    return f"({body}){' ' if space else ''}$" if sign else f"{body}{' ' if space else ''}$"


def _grams(value: Fraction) -> str:
    return f"{value:.1f}".replace(".", ",").removesuffix(",0") + "g"


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    cols = PAPER[paper_mm]["columns"]
    r = Receipt(columns=cols)
    cannabis = rng.random() < 0.5
    space = not cannabis  # '37,50 $' at the alcohol store, '42,90$' at the cannabis store
    banner = rng.choice(CANNABIS_BANNERS if cannabis else ALCOHOL_BANNERS)
    city, letter = rng.choice(CITIES)
    street = f"{rng.randint(10, 3999)}, {rng.choice(STREETS)}"
    postal = fake_postal_code(rng, letter)
    when = random_datetime(rng)
    number = f"{rng.randint(10_000, 199_999)}"
    store = f"{rng.randint(10_000, 99_999)}"
    register = rng.randint(1, 4)
    cashier = f"{rng.randint(100_000, 2_999_999)}"
    if cannabis:
        # Printed with 8 digits on the observed receipts; kept as printed.
        gst_number = _digits_failing_luhn(rng, 8) + "RT0001"
        qst_number = _digits_failing_luhn(rng, 8) + "TQ0001"
        phone = f"844555{rng.randint(100, 199):04d}"
    else:
        gst_number = fake_gst_number(rng)
        qst_number = fake_qst_number(rng)[:10] + f"TQ{rng.randint(1, 9999):04d}"
        phone = f"819-555-{rng.randint(100, 199):04d}"
    reprint = not cannabis and rng.random() < 0.2

    items, declared, shelf = [], Fraction(0), {}
    for _ in range(rng.randint(1, 5)):
        if cannabis:
            desc, grams, lo, hi = rng.choice(CANNABIS)
            if declared + grams > POSSESSION_LIMIT_G:
                continue
            declared += grams
        else:
            desc, lo, hi = rng.choice(ALCOHOL)
        if desc not in shelf:  # a product bought twice prints twice, same code and price
            code = f"{rng.randint(10**11, 10**12 - 1)}" if cannabis else f"{rng.randint(10**7, 10**8 - 1)}"
            shelf[desc] = (code, shelf_price(rng, lo, hi, cannabis))
        code, unit = shelf[desc]
        items.append({"kind": "product", "code": code, "description": desc, "qty": 1,
                      "unit_price_cents": unit, "line_total_cents": unit, "tax_flags": None})
    if not items:
        desc, grams, lo, hi = CANNABIS[0]
        declared = grams
        unit = shelf_price(rng, lo, hi, True)
        items.append({"kind": "product", "code": f"{rng.randint(10**11, 10**12 - 1)}", "description": desc,
                      "qty": 1, "unit_price_cents": unit, "line_total_cents": unit, "tax_flags": None})
    total = sum(i["line_total_cents"] for i in items)
    gst = round_half_up(total * GST_SHARE)
    qst = round_half_up(total * QST_SHARE)

    if cannabis:
        r.add(banner, align=Align.CENTER, bold=True, size=Size.DOUBLE)
        r.add(street, align=Align.CENTER)
        r.add(f"{city}, QC {postal}", align=Align.CENTER)
        r.add("Canada", align=Align.CENTER)
        r.add(phone, align=Align.CENTER)
        r.add()
        half = cols // 2 - 1
        r.add(f"{'Transaction : ' + number:<{half}} Caisse {register}")
        r.add(f"{'Magasin : ' + store:<{half}} Caissier : {cashier}")
        r.add(f"{when:Date : %d/%m/%Y}".ljust(half) + f" {when:Heure : %H:%M}")
    else:
        alcohol_header(r, banner, street, city, postal, phone, number, store, register, cashier, when)
    r.add()
    if reprint:
        reprint_banner(r)
        r.add()

    qty_end, price_end = cols * 19 // 42, cols * 31 // 42
    r.add(f"{'Article':<{qty_end - 3}}Qté{'Prix':>{price_end - qty_end}}{'Montant':>{cols - price_end}}")
    for item in items:
        r.add(item["description"][:cols])
        price = _fr(item["unit_price_cents"], space)
        r.add(f"{item['code']:<{qty_end - 2}}{item['qty']:>2}{price:>{price_end - qty_end}}"
              f"{_fr(item['line_total_cents'], space):>{cols - price_end}}")
    r.add()
    r.add(f"{'Total':>{price_end}}{_fr(total, space):>{cols - price_end}}")
    for digits, label, cents in ((gst_number, "TPS", gst), (qst_number, "TVQ", qst)):
        number_part = f"{digits[:-6]} {digits[-6:]}"
        left = f"{number_part} {label} (incl.)"
        if len(left) > price_end:
            r.add(left)
            r.add(_fr(cents, space).rjust(cols))
        else:
            r.add(f"{left:>{price_end}}{_fr(cents, space):>{cols - price_end}}")
    r.add()

    method = rng.choices(["cash", "debit", "mixed"], weights=[2, 3, 0 if cannabis else 1])[0]
    tenders, card, change = [], None, None
    if method in ("cash", "mixed"):
        cash = total if method == "cash" else rng.randrange(1000, max(1100, total - 500), 1000)
        if method == "cash" and rng.random() < 0.8:
            cash = (total // 2000 + 1) * 2000 if rng.random() < 0.5 else (total // 500 + 1) * 500
        change = cash - total if method == "cash" else 0
        tenders.append({"method": "cash", "cents": cash})
    if method in ("debit", "mixed"):
        paid = cash if method == "mixed" else 0
        tenders.append({"method": "debit", "cents": total - paid})

    rule = "_" * cols
    if cannabis:
        r.add(rule)
        if method == "cash":
            r.two_columns("Comptant", _fr(tenders[0]["cents"], False))
            r.add(rule)
            r.add("Monnaie")
            r.two_columns("Comptant", _fr(-change, False))
        else:
            r.two_columns("Debit Card", _fr(total, False))
            auth = f"{rng.randint(100_000, 999_999)}"
            last4 = f"{rng.randint(0, 9999):04d}"
            r.add(f"      {'*' * 13}{last4}")
            r.add(f"      Numéro d'autorisation : {auth}")
            r.add("      Type de transaction : Vente")
            r.add(f"      Heure d'autorisation : {when:%H:%M}")
            r.add(f"TPV 4.2.13 - MAG {rng.randint(10_000, 19_999)} - PROC. DOH")
            card = _terminal.releve_slip(r, rng, total, when, number, last4)
            r.add(rule)
            r.two_columns("Monnaie", _fr(0, False))
            change = 0
        r.add("Rendez-vous sur :")
        r.add("   information-cannabis.example pour de")
        r.add("l'information sur la consommation à")
        r.add("moindre risque.")
        r.add()
        r.add(f"Nombre d'articles vendus = {len(items)}")
        r.add(f"Poids total Articles vendus =  {_grams(declared)}")
    else:
        for tender in tenders:
            label = "Comptant" if tender["method"] == "cash" else "ACHAT DÉBIT"
            r.two_columns(label, _fr(tender["cents"], True))
        r.add()
        change = change or 0  # printed even when no cash was given
        r.two_columns("Remise Comptant", _fr(change, True))
        r.add("Taxe spécifique sur les boissons", align=Align.CENTER)
        r.add("alcooliques incluse", align=Align.CENTER)
        r.add()
        r.add(f"Nombre d'articles vendus = {len(items)}")
        if reprint:
            reprint_banner(r)
    alnum = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
    code = "T" + "".join(rng.choice(alnum) for _ in range(21))
    r.add()
    r.barcode(code)
    r.add(code, align=Align.CENTER)
    r.add()
    r.add("Exemplaire client" if cannabis else "Copie client", align=Align.CENTER)
    r.add()
    r.add("SPÉCIMEN - synthetic-receipts-canada", align=Align.CENTER)

    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "crown_store_tax_included",
        "variant": "cannabis" if cannabis else "alcohol",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": banner,
                     "address_lines": [street if cannabis else f"{street} - {city}", f"{city}, QC {postal}"],
                     "phone": phone},
        "store_number": store,
        "datetime": when.replace(second=0).isoformat(),
        "transaction_number": number,
        "items": items,
        "taxes_included": True,
        "subtotal_cents": total - gst - qst,
        "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "included": True, "cents": gst},
                  {"kind": "QST", "label": "TVQ", "rate": "0.09975", "included": True, "cents": qst}],
        "total_cents": total,
        "tip_cents": None,
        "gst_number": gst_number,
        "qst_number": qst_number,
        "payment_method": method,
        "tenders": tenders,
        "change_cents": change,
        "card": card,
        "reprint": reprint,
        "declared_weight_g": _grams(declared) if cannabis else None,
        "document_kind": "sales_receipt",
        "text_lines": r.text_lines(),
    }
    return r, truth
