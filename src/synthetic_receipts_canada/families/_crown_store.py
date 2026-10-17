"""Pieces shared by the crown-store sales receipt and its separate terminal slip."""

import random
from datetime import datetime, timedelta

from ..layout import Align, Receipt, Size

ALCOHOL_BANNERS = ["CELLIER FICTIF", "ALCOOLS DOH", "VINS SPECIMEN"]
# (description, low, high in cents)
ALCOHOL = [
    ("ROUGE DOMAINE FICTIF", 1295, 2995), ("BLANC CLOS DOH", 1395, 2495), ("ROSE DU QUIDAM", 1195, 1895),
    ("RHUM BLANC SPECIMEN", 2700, 4800), ("VODKA DOH 1,14 L", 3900, 5600), ("GIN ARTISANAL FICTIF", 3500, 5200),
    ("MOUSSEUX BRUT EXEMPLE", 1695, 3295), ("BIERE IPA DOH 4X473", 1199, 1599), ("CIDRE DE GLACE FICTIF", 2200, 3500),
]


def shelf_price(rng: random.Random, lo: int, hi: int, cannabis: bool) -> int:
    """Shelf prices end in a multiple of 5 cents, so cash needs no rounding."""
    endings = [90, 90, 95, 0, 50] if cannabis else [95, 95, 0, 25, 50, 75]
    return rng.randint(lo // 100, hi // 100 - 1) * 100 + rng.choice(endings)


def random_datetime(rng: random.Random) -> datetime:
    day = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 365 * 2 + 300))
    return day.replace(hour=rng.randint(10, 21), minute=rng.randint(0, 59), second=rng.randint(0, 59))


def reprint_banner(r: Receipt) -> None:
    stars = "*" * r.columns
    middle = " RÉIMPRESSION - RÉIMPRESSION "
    r.add(stars)
    r.add(stars)
    r.add(middle.center(r.columns, "*")[:r.columns])
    r.add(stars)
    r.add(stars)


def alcohol_header(r: Receipt, banner: str, street: str, city: str, postal: str, phone: str,
                   number: str, store: str, register: int, cashier: str, when: datetime) -> None:
    r.add(banner, align=Align.CENTER, bold=True, size=Size.DOUBLE)
    r.add()
    r.add(f"{street} - {city}", align=Align.CENTER)
    r.add(f"{city}, QC {postal}", align=Align.CENTER)
    r.add(phone, align=Align.CENTER)
    r.add()
    half = r.columns // 2 - 1
    r.add(f"{'Billet : ' + number:<{half}} Caisse : {register}")
    r.add(f"{'Succursale : ' + store:<{half}} Caissier : {cashier}")
    r.add(f"{when:Date : %Y/%m/%d}".ljust(half) + f" {when:Heure : %H:%M}")
