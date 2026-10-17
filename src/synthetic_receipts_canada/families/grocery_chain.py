"""Receipt from a large Québec grocery chain, with the payment terminal slip printed inline.

Structure observed on real 2026 receipts of one chain (see docs/templates/grocery-chain.md);
no real banner, store, number or name is reproduced. Grocery stores are outside mandatory
billing, so there is no WEB-SRM block. What makes this family hard for an extractor: two
amount columns, tax lines carrying a base and a rate before the tax, GST and QST bases that
differ, cash rounding to 5 cents, and four date formats on one receipt.
"""

import random
import unicodedata
from datetime import datetime, timedelta
from fractions import Fraction

from .. import SCHEMA_VERSION
from ..fakes import CITIES, STREETS, fake_full_name, fake_gst_number, fake_qst_number
from ..layout import Align, Receipt, Size
from ..money import GST_RATE, QST_RATE, format_cad_en, round_half_up
from ..render import PAPER

BANNERS = ["MARCHE DOH", "EPICERIE FICTIVE", "SUPER SPECIMEN", "ECONO-DOH", "PANIER FICTIF", "ALIMENTATION DOH"]

# (department, description, low cents, high cents, flags, kind). F = GST, P = QST; the other
# letters are chain-specific and tax-neutral. kind: unit, weight (price per kg), drink (deposit).
CATALOG = [
    ("21-EPICERIE", "DET LIQ HE 2L", 799, 1499, "FPMRJ", "unit"),
    ("21-EPICERIE", "SAVON VAISS CITR", 199, 399, "FPMRJ", "unit"),
    ("21-EPICERIE", "CROUST BBQ GF", 250, 450, "FPMRJ", "unit"),
    ("21-EPICERIE", "BOISS GAZ COLA", 400, 1599, "FPMRJ", "drink"),
    ("21-EPICERIE", "BOISS GAZ FRAISE", 199, 299, "FPMRJ", "drink"),
    ("21-EPICERIE", "NOURR CHAT 7KG", 1400, 4500, "FPMRJ", "unit"),
    ("21-EPICERIE", "LITIERE AGGL 14KG", 999, 1199, "FPMRJ", "unit"),
    ("21-EPICERIE", "PAPIER HYG 24R", 1500, 2400, "FMRJ", "unit"),
    ("21-EPICERIE", "THON PALE EAU", 100, 229, "MRJ", "unit"),
    ("21-EPICERIE", "CEREALES FRUITS", 450, 900, "MRJ", "unit"),
    ("21-EPICERIE", "BEURRE ARACH CR", 450, 650, "MRJ", "unit"),
    ("21-EPICERIE", "JUS POMME 1.89L", 169, 349, "MRJ", "unit"),
    ("21-EPICERIE", "CAFE MOULU MOY", 999, 1988, "MRJ", "unit"),
    ("22-PRODUITS LAITIERS", "LAIT 2% 4L", 699, 899, "RQ", "unit"),
    ("22-PRODUITS LAITIERS", "BABEURRE 1L", 299, 445, "RQ", "unit"),
    ("22-PRODUITS LAITIERS", "YOGOURT GREC 750G", 329, 599, "MRJ", "unit"),
    ("23-PRODUITS SURGELES", "PIZZA PEPP SURG", 400, 698, "MRJ", "unit"),
    ("23-PRODUITS SURGELES", "FRITES COUPE REG", 300, 450, "MRJ", "unit"),
    ("23-PRODUITS SURGELES", "BARRE GLACEE VAN", 400, 579, "FMRJ", "unit"),
    ("23-PRODUITS SURGELES", "CORNET AMANDE", 500, 650, "FMRJ", "unit"),
    ("23-PRODUITS SURGELES", "LASAGNE VIANDE", 899, 1350, "MRJ", "unit"),
    ("27-FRUITS ET LEGUMES", "TOMATES", 329, 549, "MRJ", "weight"),
    ("27-FRUITS ET LEGUMES", "OIGNON ESPAGNOL", 299, 449, "MRJ", "weight"),
    ("27-FRUITS ET LEGUMES", "BANANES", 145, 199, "MRJ", "weight"),
    ("27-FRUITS ET LEGUMES", "POMMES CORTLAND", 329, 549, "MRJ", "weight"),
    ("31-VIANDE", "POITRINE POULET", 1000, 2200, "MRJ", "unit"),
    ("31-VIANDE", "BOEUF HACHE MI-M", 699, 1499, "MRJ", "unit"),
    ("33-BOULANGERIE", "MUFFINS CHOCO 6", 499, 699, "FMRJ", "unit"),
    ("33-BOULANGERIE", "BISC BR ARACH", 399, 599, "MRJ", "unit"),
    ("34-BOULANGERIE COMMERCIALE", "PAIN BLANC TR", 300, 500, "MRJ", "unit"),
    ("35-CHARCUTERIE", "FROMAGE GRAINS 600G", 900, 1500, "MRJ", "unit"),
    ("35-CHARCUTERIE", "JAMBON TR MINCE", 500, 800, "MRJ", "unit"),
    ("41-MAISON", "PELLE LITIERE", 300, 500, "FPMRJ", "unit"),
    ("41-MAISON", "SACS POUBELLE 40", 699, 1299, "FPMRJ", "unit"),
]
FREE_STAMP = ("41-MAISON", "TIMBRE CONCOURS", "Q")
DEPOSIT_UNITS = [10, 60, 120, 240]  # one can, a 6-pack, a 12-pack, a 24-pack
CARD_NETWORKS = {
    "debit": ("Interac", "A0000002771010"),
    "visa": ("Visa", "A0000000031010"),
    "mastercard": ("Mastercard", "A0000000041010"),
}


def _plain(text: str) -> str:
    """The chain's printer has no accents: SAINT-JEROME, not SAINT-JÉRÔME."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()


def _amt(cents: int) -> str:
    return f"({_amt(-cents)})" if cents < 0 else f"{cents // 100}.{cents % 100:02d}"


def _cash_rounded(cents: int) -> int:
    """Canadian penny rounding: to the nearest 5 cents, x.x3 up, x.x2 down."""
    return (cents + 2) // 5 * 5


def _shelf_price(rng: random.Random, lo: int, hi: int) -> int:
    """A price as shelves show them: whole dollars plus a usual ending (.99, .49, .00...)."""
    dollars = rng.randint(lo // 100, max(lo // 100, hi // 100 - 1))
    return dollars * 100 + rng.choice([0, 25, 49, 50, 75, 79, 88, 98, 99])


def _random_datetime(rng: random.Random) -> datetime:
    day = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 365 * 2 + 300))
    return day.replace(hour=rng.randint(8, 21), minute=rng.randint(0, 59), second=rng.randint(0, 59))


def _pick_items(rng: random.Random) -> list[dict]:
    items = []
    for _ in range(rng.randint(2, 18)):
        dept, desc, lo, hi, flags, kind = rng.choice(CATALOG)
        item = {"kind": "product", "department": dept, "code": None, "description": desc,
                "qty": 1, "unit_price_cents": None, "weight_kg": None, "promo": None,
                "line_total_cents": 0, "tax_flags": flags}
        if kind == "weight":
            item["code"] = f"{rng.randint(3000, 4999)}"
            grams = rng.randint(150, 2400)
            unit = _shelf_price(rng, lo, hi)
            item["weight_kg"] = f"{grams / 1000:.3f}"
            item["unit_price_cents"] = unit
            item["line_total_cents"] = round_half_up(Fraction(grams * unit, 1000))
        else:
            item["code"] = f"0{rng.randint(10**9, 10**10 - 1)}"
            unit = _shelf_price(rng, lo, hi)
            qty = 1 if rng.random() < 0.7 else rng.choice([2, 2, 2, 3, 3, 4, 6, 10])
            if kind == "drink":
                qty = min(qty, 3)
            if qty > 1 and rng.random() < 0.3:
                regular = unit + rng.choice([50, 75, 100])
                item["promo"] = {"limit": rng.choice([6, 12]), "regular_cents": regular}
            item["qty"] = qty
            item["unit_price_cents"] = unit
            item["line_total_cents"] = unit * qty
        items.append(item)
        if kind == "drink":
            per = rng.choice(DEPOSIT_UNITS)
            items.append({"kind": "deposit", "department": dept, "code": None, "description": "CONSIGNE 1",
                          "qty": item["qty"], "unit_price_cents": per, "weight_kg": None, "promo": None,
                          "line_total_cents": per * item["qty"], "tax_flags": ""})
    if rng.random() < 0.1:
        dept, desc, flags = FREE_STAMP
        qty = rng.randint(1, 8)
        items.append({"kind": "product", "department": dept, "code": f"{rng.randint(10000, 99999)}",
                      "description": desc, "qty": qty, "unit_price_cents": 0, "weight_kg": None,
                      "promo": None, "line_total_cents": 0, "tax_flags": flags})
    # Printed grouped by department, in department-number order; a deposit stays under its drink.
    order = {d: i for i, d in enumerate(sorted({i["department"] for i in items}))}
    groups: list[list[dict]] = []
    for item in items:
        if item["kind"] == "deposit":
            groups[-1].append(item)
        else:
            groups.append([item])
    groups.sort(key=lambda g: order[g[0]["department"]])
    return [item for group in groups for item in group]


def _item_lines(r: Receipt, item: dict) -> None:
    cols = r.columns
    if item["kind"] == "deposit":
        r.add(f"   {item['description']}")
        if item["qty"] > 1:
            r.add(f"   {item['qty']}@{format_cad_en(item['unit_price_cents'])}")
        r.add(_amt(item["line_total_cents"]).rjust(cols))
        return
    code = item["code"] if item["qty"] == 1 or item["weight_kg"] else f"({item['qty']}){item['code']}"
    desc = item["description"][:17]
    head = f"  {code:<14} {desc}"
    simple = item["qty"] == 1 and not item["weight_kg"]
    inline_flags = "P" not in item["tax_flags"]
    if simple and inline_flags and cols >= 40:
        # Middle amount column: ends four columns short of the right edge.
        r.add(f" {code:<11} {item['description'][:12]:<12} {item['tax_flags']:<5}{_amt(item['line_total_cents']):>7}")
        return
    if inline_flags and cols >= 40:
        r.add(f"{head} {item['tax_flags']}")
    else:
        r.add(head[:cols])
        r.add(f"{'':>12}{item['tax_flags']}")
    if item["weight_kg"]:
        r.two_columns(f"    {item['weight_kg']} kg @ {format_cad_en(item['unit_price_cents'])}/kg",
                      _amt(item["line_total_cents"]))
        return
    if item["promo"]:
        promo = item["promo"]
        r.add(f"   {format_cad_en(item['unit_price_cents'])} lmt {promo['limit']}, "
              f"{format_cad_en(promo['regular_cents'])} ch")
        r.two_columns(f"   {item['qty']} @ {format_cad_en(item['unit_price_cents'])} ch", _amt(item["line_total_cents"]))
    elif item["qty"] > 1:
        r.two_columns(f"   {item['qty']} @ {format_cad_en(item['unit_price_cents'])}", _amt(item["line_total_cents"]))
    else:
        r.add(_amt(item["line_total_cents"]).rjust(cols))


def _card_slip(r: Receipt, rng: random.Random, method: str, network: str, cents: int, when: datetime,
               garbled: bool) -> dict:
    name, aid = CARD_NETWORKS[network]
    e = (lambda word: word.replace("é", ",").replace("É", " ")) if garbled else (lambda word: word)
    last4 = f"{rng.randint(0, 9999):04d}"
    if method == "debit":
        account = rng.choice(["DEFAUT", "CHEQUE"])
        suffix = "P" if account == "DEFAUT" else "C"
        card_type, ref = e("DÉBIT"), f"00100{rng.randint(10000, 99999)}"
        approval = "00/001 APPROUVEE - MERCI"
        tail = f"{aid} {rng.choice(['8000008000', '0080008000 EC00'])}"
    else:
        account, suffix = name.upper(), "P"
        card_type, ref = "CREDIT", f"{rng.randint(100000, 999999)}"
        approval = "00 APPROUVEE - MERCI"
        tail = f"{aid} 0000000000"
    at = when + timedelta(seconds=rng.randint(5, 50))
    auth = "".join(rng.choice("0123456789ABCDEF") for _ in range(6))
    amount = f"{cents // 100},{cents % 100:02d} CAD$"
    r.add()
    r.add("Type de Trans.:  ACHAT")
    r.add(f"Compte:  {account:<18}{amount}")
    r.add(f"Type de carte:  {card_type}")
    r.add(f"{e('Numéro')} de Carte:  {'*' * 12}{last4} {suffix}")
    r.add(f"DateTime:        {at:%y/%m/%d %H:%M:%S}")
    r.add(f"# de Ref.:       {ref}")
    r.add(f"# d'Autor.:      {auth}")
    r.add(name)
    r.add(tail)
    r.add(approval, align=Align.CENTER)
    if method == "debit" and rng.random() < 0.3:
        r.add("VERIFIEE PAR NIP", align=Align.CENTER)
    r.add(f"Conservez cette copie pour {e('vérification')}", align=Align.CENTER)
    r.add("de votre rapport financier", align=Align.CENTER)
    r.add("*** COPIE DU CLIENT ***", align=Align.CENTER)
    r.add()
    r.two_columns("   DEBIT" if method == "debit" else "   CREDIT", _amt(cents))
    return {"network": name, "masked_number": f"{'*' * 12}{last4}", "account": account,
            "datetime": at.isoformat(), "reference": ref, "authorization": auth}


def generate(rng: random.Random, paper_mm: int = 80) -> tuple[Receipt, dict]:
    r = Receipt(columns=PAPER[paper_mm]["columns"])
    banner = rng.choice(BANNERS)
    city, _ = rng.choice(CITIES)
    store = f"{rng.randint(1000, 9999)}"
    lane = f"{rng.randint(201, 420)}"
    form_a = rng.random() < 0.5
    phone = f"{rng.choice(['819', '418', '450', '514'])}-555-{rng.randint(100, 199):04d}"
    address = f"{rng.randint(10, 3999)},{_plain(rng.choice(STREETS).split(' ', 1)[1])}, {_plain(city)}"
    gst_number = fake_gst_number(rng)[:9] + f"RT{rng.choice([1, 1, 5]):04d}"
    qst_number = fake_qst_number(rng)[:10] + f"TQ{rng.choice([1, 2]):04d}" if rng.random() < 0.6 else None
    when = _random_datetime(rng)
    self_checkout = rng.random() < 0.25
    transaction = f"{rng.randint(0, 9999):04d}"

    items = _pick_items(rng)
    subtotal = sum(i["line_total_cents"] for i in items)
    gst_base = sum(i["line_total_cents"] for i in items if "F" in i["tax_flags"])
    qst_base = sum(i["line_total_cents"] for i in items if "P" in i["tax_flags"])
    gst = round_half_up(Fraction(gst_base) * GST_RATE)
    qst = round_half_up(Fraction(qst_base) * QST_RATE)
    total = subtotal + gst + qst

    r.add(banner, align=Align.CENTER, bold=True, size=Size.DOUBLE)
    r.add()
    if form_a:
        r.add(f"{banner} {_plain(city)} ({store})")
        r.add(address)
    else:
        r.add(f"{banner} {_plain(city)}")
        r.add(phone)
    r.add()
    department = None
    for item in items:
        if item["department"] != department:
            department = item["department"]
            r.add(department, bold=True)
        _item_lines(r, item)
    r.two_columns("SOUS-TOTAL", _amt(subtotal), bold=True, size=Size.DOUBLE)
    r.add(f"   F=T.P.S 5%  {_amt(gst_base):>6} @  5.000%")
    r.add(_amt(gst).rjust(r.columns))
    r.add(f"   P=TVQ 9.975% {_amt(qst_base):>6} @  9.975%")
    r.add(_amt(qst).rjust(r.columns))
    r.two_columns("TOTAL", _amt(total), bold=True, size=Size.DOUBLE)
    if rng.random() < 0.3:
        count = sum(i["qty"] for i in items if i["kind"] == "product")
        r.add(f"NOMBRE D'ARTICLES:     {count}")

    tenders, card, rounding, change = [], None, None, None
    method = rng.choices(["cash", "debit", "credit", "mixed"], weights=[3, 5, 2, 1])[0]
    garbled = rng.random() < 0.5
    if method == "cash":
        rounded = _cash_rounded(total)
        rounding = rounded - total
        given = rounded if rng.random() < 0.2 else (rounded // 500 + 1) * 500 if rng.random() < 0.5 else (rounded // 100 + 1) * 100
        change = given - rounded
        r.add()
        r.two_columns("     COMPTANT", _amt(given))
        if rounding:
            r.two_columns(f"     ARRONDI {_amt(abs(rounding))}", _amt(-rounded))
        if change:
            r.two_columns("     MONNAIE", _amt(change), bold=True, size=Size.DOUBLE)
        tenders.append({"method": "cash", "cents": given})
    else:
        card_cents = total
        if method == "mixed":
            cash = rng.randrange(2000, max(2100, total - 500), 1000) if total > 2600 else 1000
            cash = min(cash, total - 100)
            card_cents = total - cash
            r.add()
            r.two_columns("     COMPTANT", _amt(cash))
            tenders.append({"method": "cash", "cents": cash})
        kind = "credit" if method == "credit" else "debit"
        network = rng.choice(["visa", "mastercard"]) if kind == "credit" else "debit"
        card = _card_slip(r, rng, kind, network, card_cents, when, garbled)
        tenders.append({"method": kind, "cents": card_cents})

    points = total // 100 * 10
    r.add(f"VOUS AURIEZ PU RECOLTER AU MOINS {points:,}", align=Align.CENTER)
    r.add("POINTS FIDELITE DE PLUS GRACE A LA", align=Align.CENTER)
    r.add("CARTE DE CREDIT FICTIVE DOH.", align=Align.CENTER)
    r.add()
    r.add(f"TPS # {gst_number[:5]}-{gst_number[5:9]} {gst_number[9:]}", align=Align.CENTER)
    if qst_number:
        r.add(f"TVQ# {qst_number[:10]} {qst_number[10:12]} {qst_number[12:]}")
    title = rng.choice(["DIRECTEUR DU MAGASIN:", "DIRECTRICE DE MAGASIN"])
    r.add(f"{title} {_plain(fake_full_name(rng))}")
    if form_a:
        r.add(f"NUMERO DE TELEPHONE: {phone}")
    r.add("*" * (r.columns - 4))
    if self_checkout:
        r.add(f"{when:%y/%m/%d} LIBRE-SERV {rng.randint(1, 6)}  999{rng.randint(1, 6)}  "
              f"{rng.randint(1, 40):02d} {transaction} {when:%H:%M}")
    else:
        r.add(f"{when:%Y/%m/%d}  {lane}   {lane}   {rng.randint(1, 9):02d} {transaction}   {when:%H:%M}")
    r.add("PARTAGEZ VOTRE OPINION SUR LE MAGASIN!")
    r.add("VISITEZ OPINION.EXAMPLE OU APPELEZ")
    r.add(f"1-800-555-{rng.randint(100, 199):04d}. GAGNEZ UNE CARTE-CADEAU")
    r.add(f"CODE: {when:%m%d%y} {when:%H%M}01 {transaction} 0{store}")
    r.add()
    r.add("SPECIMEN - synthetic-receipts-canada", align=Align.CENTER)

    r.wrap_overflow()

    truth = {
        "schema_version": SCHEMA_VERSION,
        "family": "grocery_chain",
        "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
        "paper_width_mm": paper_mm,
        "merchant": {"name": banner,
                     "address_lines": [address] if form_a else [],
                     "phone": phone},
        "store_number": store if form_a else None,
        "datetime": when.replace(second=0).isoformat(),
        "transaction_number": transaction,
        "items": items,
        "subtotal_cents": subtotal,
        "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "base_cents": gst_base, "cents": gst},
                  {"kind": "QST", "label": "TVQ", "rate": "0.09975", "base_cents": qst_base, "cents": qst}],
        "total_cents": total,
        "tip_cents": None,
        "gst_number": gst_number,
        "qst_number": qst_number,
        "payment_method": method,
        "tenders": tenders,
        "cash_rounding_cents": rounding,
        "change_cents": change,
        "card": card,
        "document_kind": "sales_receipt",
        "text_lines": r.text_lines(),
    }
    return r, truth
