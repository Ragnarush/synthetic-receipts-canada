from fractions import Fraction

import pytest

from synthetic_receipts_canada.money import (cash_rounded, format_cad_en, format_cad_fr, gst_cents, qst_cents,
                                             round_half_up)


@pytest.mark.parametrize("value, expected", [
    (Fraction(5, 2), 3), (Fraction(7, 2), 4), (Fraction(-5, 2), -3), (Fraction(249, 100), 2), (Fraction(0), 0),
])
def test_round_half_up_ties_away_from_zero(value, expected):
    assert round_half_up(value) == expected


@pytest.mark.parametrize("cents, expected", [
    (1000, 1000), (1001, 1000), (1002, 1000), (1003, 1005), (1004, 1005),
    (1005, 1005), (1006, 1005), (1007, 1005), (1008, 1010), (1009, 1010),
])
def test_cash_rounded_to_nickel(cents, expected):
    assert cash_rounded(cents) == expected


def test_taxes_on_a_known_subtotal():
    # 42.10 $: GST 2.105 -> 2.11 (half up; banker's rounding would give 2.10), QST 4.199475 -> 4.20.
    assert gst_cents(4210) == 211
    assert qst_cents(4210) == 420


@pytest.mark.parametrize("cents, fr, en", [
    (0, "0,00 $", "$0.00"), (4210, "42,10 $", "$42.10"), (123456, "1 234,56 $", "$1,234.56"),
    (-205, "-2,05 $", "-$2.05"),
])
def test_formats(cents, fr, en):
    assert format_cad_fr(cents) == fr
    assert format_cad_en(cents) == en
