"""Invariants every family must hold, checked on COUNT receipts per family at each paper width.

Checks read the ground truth generically (keys like `taxes_included`, `base_cents`, `tenders`)
rather than per family, so a new family is covered as soon as it is registered; what only one
family has goes in a test named after it.
"""

import random
import re
from datetime import datetime
from fractions import Fraction

import pytest

from synthetic_receipts_canada import REPO_URL, SCHEMA_VERSION
from synthetic_receipts_canada.families import FAMILIES
from synthetic_receipts_canada.fakes import LAST_NAMES, luhn_is_valid
from synthetic_receipts_canada.money import cash_rounded, round_half_up
from synthetic_receipts_canada.render import PAPER

from conftest import PAPERS, sample

COMMON_KEYS = {
    "schema_version", "family", "country", "province", "currency", "language", "paper_width_mm", "merchant",
    "datetime", "transaction_number", "items", "subtotal_cents", "taxes", "total_cents", "tip_cents",
    "gst_number", "qst_number", "payment_method", "document_kind", "text_lines",
}
DOCUMENT_KINDS = {"sales_receipt", "original_invoice", "closing_receipt", "payment_slip", "invoice"}
# On 58 mm the line wraps after the dash, as the printer would.
SPECIMEN = re.compile(r"^ *SP[ÉE]CIMEN -\s+synthetic-receipts-canada *$", re.MULTILINE)
FR_MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

CASES = [(family, paper) for family in FAMILIES for paper in PAPERS]


def receipts(family: str, paper: int):
    for index, (receipt, truth) in enumerate(sample(family, paper), start=1):
        yield f"{family} #{index:04d} at {paper} mm", receipt, truth


def amount_pattern(cents: int) -> re.Pattern:
    """An amount as any family prints it: 1234.56, 1234,56, 1 234,56, 1,234.56 (sign and $ aside)."""
    dollars, rest = divmod(abs(cents), 100)
    forms = {f"{dollars}.{rest:02d}", f"{dollars},{rest:02d}",
             f"{dollars:,}".replace(",", " ") + f",{rest:02d}", f"{dollars:,}.{rest:02d}"}
    return re.compile(rf"(?<![\d.,])(?:{'|'.join(map(re.escape, forms))})(?!\d)")


def date_forms(when: datetime) -> set[str]:
    return {f"{when:%Y-%m-%d}", f"{when:%Y/%m/%d}", f"{when:%y/%m/%d}", f"{when:%d/%m/%Y}",
            f"{when:%d/%m/%y}", f"{when:%m/%d/%y}", f"{when:%m%d%y}",
            f"{when.day}-{FR_MONTHS[when.month - 1]}-{when.year}"}


def printed(text: str, value: str) -> bool:
    """`value` printed as its own run of digits, not inside a longer one."""
    return re.search(rf"(?<!\d){re.escape(value)}(?!\d)", text) is not None


def leading_digits(number: str) -> str:
    return re.match(r"\d+", number).group()


@pytest.mark.parametrize("family, paper", CASES)
def test_ground_truth_shape(family, paper):
    for where, receipt, truth in receipts(family, paper):
        assert COMMON_KEYS <= truth.keys(), f"{where}: missing {COMMON_KEYS - truth.keys()}"
        assert truth["schema_version"] == SCHEMA_VERSION, where
        assert truth["family"] == family, where
        assert truth["document_kind"] in DOCUMENT_KINDS, where
        assert truth["paper_width_mm"] in PAPER, where
        assert receipt.columns == PAPER[truth["paper_width_mm"]]["columns"], where
        assert truth["text_lines"] == receipt.text_lines(), where
        datetime.fromisoformat(truth["datetime"])


@pytest.mark.parametrize("family, paper", CASES)
def test_lines_fit_the_paper(family, paper):
    for where, receipt, truth in receipts(family, paper):
        for line in receipt.lines:
            width = receipt.columns // line.size.value
            assert len(line.text) <= width, f"{where}: {len(line.text)} > {width} columns: {line.text!r}"


@pytest.mark.parametrize("family, paper", CASES)
def test_arithmetic(family, paper):
    for where, _, truth in receipts(family, paper):
        items, total, taxes = truth["items"], truth["total_cents"], truth["taxes"]
        for item in items:
            if item.get("weight_kg"):
                grams = round(Fraction(item["weight_kg"]) * 1000)
                expected = round_half_up(Fraction(grams * item["unit_price_cents"], 1000))
            else:
                expected = item["qty"] * item["unit_price_cents"]
            assert item["line_total_cents"] == expected, f"{where}: {item}"
        if total is None:
            assert truth["subtotal_cents"] is None and not taxes and not items, where
            continue
        tax_sum = sum(t["cents"] for t in taxes)
        if truth.get("taxes_included"):
            gross = 1 + sum(Fraction(t["rate"]) for t in taxes)
            for tax in taxes:
                assert tax["cents"] == round_half_up(total * Fraction(tax["rate"]) / gross), f"{where}: {tax}"
            assert sum(i["line_total_cents"] for i in items) == total, where
            assert truth["subtotal_cents"] == total - tax_sum, where
        else:
            subtotal = truth["subtotal_cents"]
            assert sum(i["line_total_cents"] for i in items) == subtotal, where
            for tax in taxes:
                base = tax.get("base_cents", subtotal)
                assert tax["cents"] == round_half_up(base * Fraction(tax["rate"])), f"{where}: {tax}"
            assert total == subtotal + tax_sum, where


@pytest.mark.parametrize("family, paper", CASES)
def test_payments(family, paper):
    for where, _, truth in receipts(family, paper):
        if "tenders" not in truth:
            continue
        tenders, total = truth["tenders"], truth["total_cents"]
        rounding = truth.get("cash_rounding_cents") or 0
        change = truth.get("change_cents") or 0
        cash = sum(t["cents"] for t in tenders if t["method"] == "cash")
        assert all(t["cents"] > 0 for t in tenders), f"{where}: {tenders}"
        # Cash changes hands in multiples of 5 cents since the cent was withdrawn.
        assert all(t["cents"] % 5 == 0 for t in tenders if t["method"] == "cash"), f"{where}: {tenders}"
        assert change >= 0, where
        assert cash or not change, f"{where}: change without cash"
        if total is None:  # a card slip carries no purchase total
            continue
        assert sum(t["cents"] for t in tenders) == total + rounding + change, where
        # Only the cash share rounds to 5 cents; the total keeps its cents.
        cash_share = total - sum(t["cents"] for t in tenders if t["method"] != "cash")
        expected = cash_rounded(cash_share) - cash_share if cash else 0
        if truth.get("cash_rounding_cents") is not None or expected:
            assert rounding == expected, f"{where}: rounding {rounding}, expected {expected}"


@pytest.mark.parametrize("family, paper", CASES)
def test_printed_values_match_ground_truth(family, paper):
    for where, _, truth in receipts(family, paper):
        text = "\n".join(truth["text_lines"])
        alnum = re.sub(r"[^0-9A-Za-z]", "", text)
        amounts = [i["line_total_cents"] for i in truth["items"]]
        amounts += [t["cents"] for t in truth["taxes"]] + [t["base_cents"] for t in truth["taxes"] if "base_cents" in t]
        amounts += [t["cents"] for t in truth.get("tenders", [])]
        if not truth.get("taxes_included"):
            amounts.append(truth["subtotal_cents"])  # an included-tax receipt prints no subtotal
        amounts += [truth["total_cents"], truth["tip_cents"], truth.get("change_cents") or None]
        for cents in amounts:
            if cents is not None:
                assert amount_pattern(cents).search(text), f"{where}: amount {cents} not printed"

        # null means absent from the receipt: whatever the merchant block holds must be printed.
        flat = " ".join(text.split())
        merchant = truth["merchant"]
        for value in [merchant["name"], *merchant["address_lines"], merchant["phone"]]:
            if value:
                assert " ".join(value.split()) in flat, f"{where}: merchant {value!r} not printed"

        when = datetime.fromisoformat(truth["datetime"])
        assert any(form in text for form in date_forms(when)), f"{where}: date {when:%Y-%m-%d} not printed"
        if "T" in truth["datetime"]:
            assert f"{when:%H:%M}" in text, f"{where}: time not printed"

        for key in ("transaction_number", "store_number", "associate_id"):
            if truth.get(key):
                assert printed(text, truth[key]), f"{where}: {key} {truth[key]} not printed"
        for key in ("gst_number", "qst_number"):
            if truth[key]:
                assert truth[key] in alnum, f"{where}: {key} {truth[key]} not printed"
        if truth.get("card"):
            card = truth["card"]
            assert card["masked_number"] in text, where
            for masked in re.finditer(r"\*{4,}(\d{4})", text):  # every masked number is this card
                assert masked.group(1) == card["masked_number"][-4:], f"{where}: {masked.group()}"
            assert card["authorization"] in text, where
            assert card["reference"] in text, where
            at = datetime.fromisoformat(card["datetime"])
            assert any(form in text for form in date_forms(at)) and f"{at:%H:%M:%S}" in text, where


@pytest.mark.parametrize("family, paper", CASES)
def test_guardrails(family, paper):
    for where, receipt, truth in receipts(family, paper):
        text = "\n".join(truth["text_lines"])
        assert SPECIMEN.search(text), f"{where}: no SPÉCIMEN line"
        for key in ("gst_number", "qst_number"):
            if truth[key]:
                assert not luhn_is_valid(leading_digits(truth[key])), f"{where}: {key} passes Luhn"
        phone = re.sub(r"\D", "", truth["merchant"]["phone"] or "")
        assert not phone or (phone[-7:-4] == "555" and phone[-4:-2] == "01"), f"{where}: phone {phone}"
        # An area code, then 555: not a device id (1555-2345-...) or a tax number (12555-6789).
        for match in re.finditer(r"(?:\(\d{3}\)|(?<!\d)\d{3}[ -])555-(\d{4})", text):
            assert match.group(1).startswith("01"), f"{where}: {match.group()} outside 555-01XX"
        assert not re.search(r"(?i)\bwww\.|[\w-]\.(?:com|ca|net|org)\b", text), f"{where}: real-looking URL"
        for line in receipt.lines:
            if line.qr_payload is not None:
                assert line.qr_payload.startswith(REPO_URL), f"{where}: QR {line.qr_payload}"
        if truth.get("client"):
            assert truth["client"]["name"].split()[-1] in LAST_NAMES, where
        for match in re.finditer(r"DIRECT(?:EUR|RICE) D[UE] MAGASIN:?\s+\S+\s+(\S+)", text):  # may wrap
            surname = match.group(1)
            assert surname in {n.upper() for n in LAST_NAMES} | {"SPECIMEN"}, f"{where}: {match.group()!r}"


@pytest.mark.parametrize("family", FAMILIES)
def test_same_seed_same_receipt(family):
    first = FAMILIES[family].generate(random.Random(f"7/{family}/3"))[1]
    again = FAMILIES[family].generate(random.Random(f"7/{family}/3"))[1]
    assert first == again


def test_standalone_terminal_prints_on_its_own_paper():
    for where, _, truth in receipts("payment_terminal_slip", 80):
        if truth["variant"] == "standalone_terminal":
            assert truth["paper_width_mm"] == 58, where
        else:
            assert truth["paper_width_mm"] == 80, where
