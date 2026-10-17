"""Blocks shared by every Revenu Québec mandatory-billing (WEB-SRM) receipt.

Source: Revenu Québec, « Exemple de facture – Secteur de la restauration » and the taxi
counterpart (July 2025 samples, copies under docs/sources/). The numbered elements below refer to
those samples. Content outside the two '=' separators is free (element note: a server's name, a
thank-you line, a survey); everything between them is prescribed and ordered.
"""

import random
from datetime import date, datetime

from .. import REPO_URL
from ..fakes import random_day
from ..layout import Align, Receipt, Size
from ..money import format_cad_fr

PAYMENT_METHODS = {
    "debit": "CARTE DE DÉBIT",
    "credit": "CARTE DE CRÉDIT",
    "cash": "COMPTANT",
}
THANKS = ["Merci et bonne journée", "Merci de votre visite", "Au plaisir de vous revoir", "Merci!"]


def random_datetime(rng: random.Random, hours: list[tuple[int, int]], first: date) -> datetime:
    """`first`: the day the sector's receipts took the WEB-SRM form, none before."""
    day = random_day(rng, first)
    start, end = rng.choice(hours)
    return day.replace(hour=rng.randint(start, end - 1), minute=rng.randint(0, 59), second=rng.randint(0, 59))


def websrm_ids(rng: random.Random) -> dict:
    alnum = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
    group = lambda: "".join(rng.choice(alnum) for _ in range(4))
    tx = f"{group()}-{rng.randint(0, 9999):04d}-{group()}-{rng.randint(0, 9999):04d}"
    device = f"{rng.randint(1, 9999):04d}-{rng.randint(0, 9999):04d}-{rng.randint(0, 9999):04d}"
    return {"transaction_id": tx, "device_id": device, "qr_url": f"{REPO_URL}#specimen-{tx}"}


def header(r: Receipt, name: str, address_lines: list[str], phone: str | None, rng: random.Random) -> str | None:
    """Element 1: trade name and full address. Anything else up here is optional free content.

    Returns the phone if it was printed, None otherwise.
    """
    r.add(name, align=Align.CENTER, bold=True, size=Size.DOUBLE if len(name) <= r.columns // 2 else Size.NORMAL)
    for line in address_lines:
        r.add(line, align=Align.CENTER)
    printed = phone if phone and rng.random() < 0.6 else None
    if printed:
        r.add(f"Tél. : {printed}", align=Align.CENTER)
    r.add()
    return printed


def transaction_lines(r: Receipt, when: datetime, number: str) -> None:
    """Elements 2 and 3."""
    r.add(f" {when:%Y-%m-%d %H:%M:%S}")
    r.add(f" TRANSACTION #{number}", bold=True)
    r.add()


def item_line(r: Receipt, qty: int, description: str, cents: int, flags: str) -> None:
    """Elements 4 and 5: description and the taxes that apply (F federal, P provincial, S extra)."""
    price = format_cad_fr(cents)
    left = f"{qty} {description}"
    right = f"{price} {flags:<3}"
    room = r.columns - len(right) - 1
    if len(left) > room:
        left = left[:room]
    r.add(f"{left}{' ' * (r.columns - len(left) - len(right))}{right}")


def registration_lines(r: Receipt, gst_number: str, qst_number: str) -> None:
    """Elements 7 and 8, printed the way the official sample splits them: digits, then RT/TQ 0001."""
    r.add(f" TPS: {gst_number[:9]}     {gst_number[9:11]} {gst_number[11:]}")
    r.add(f" TVQ: {qst_number[:10]}    {qst_number[10:12]} {qst_number[12:]}")
    r.add()


def amount_block(r: Receipt, gst: int, qst: int, total: int, tip: int | None, narrow: bool) -> None:
    """Elements 12 to 14 (and the tip among the optional amounts), after the first '=' run."""
    rows = [("TPS:", gst), ("TVQ:", qst), ("TOTAL:", total)]
    if tip:
        rows.append(("Pourboire:", tip))
    for label, cents in rows:
        bold = label == "TOTAL:"
        if narrow:
            r.add(f" {label:<12}{format_cad_fr(cents):>12}", bold=bold)
        else:
            r.two_columns(f" {label}", format_cad_fr(cents), bold=bold)
    r.add()


def fiscal_footer(r: Receipt, mention: str, ids: dict, processed_at: datetime) -> None:
    """Elements 15 to 20."""
    r.add(mention, align=Align.CENTER)
    r.qr(ids["qr_url"])
    r.add(f"{processed_at:%Y-%m-%d %H:%M:%S}", align=Align.CENTER)
    r.add(ids["transaction_id"], align=Align.CENTER)
    r.add(ids["device_id"], align=Align.CENTER)
    r.separator("=")
