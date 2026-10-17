"""Money as integer cents, rounded half-up like a cash register (never banker's rounding)."""

from fractions import Fraction

GST_RATE = Fraction(5, 100)
QST_RATE = Fraction(9975, 100_000)


def round_half_up(value: Fraction) -> int:
    """Round a Fraction of cents to the nearest cent, ties away from zero."""
    sign = -1 if value < 0 else 1
    magnitude = abs(value)
    whole = magnitude.numerator // magnitude.denominator
    remainder = magnitude - whole
    if remainder >= Fraction(1, 2):
        whole += 1
    return sign * whole


def gst_cents(subtotal_cents: int) -> int:
    return round_half_up(Fraction(subtotal_cents) * GST_RATE)


def qst_cents(subtotal_cents: int) -> int:
    return round_half_up(Fraction(subtotal_cents) * QST_RATE)


def cash_rounded(cents: int) -> int:
    """Canadian penny rounding of a cash payment: to the nearest 5 cents, x.x3 up, x.x2 down.

    Since the cent was withdrawn (2013) only the cash payment rounds; prices and totals keep
    their cents, and card payments are never rounded.
    """
    return (cents + 2) // 5 * 5


def format_cad_fr(cents: int) -> str:
    """French-Canadian receipt style: '1 234,56 $' (thin-space thousands, comma decimals)."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    dollars, rest = divmod(cents, 100)
    dollars_str = f"{dollars:,}".replace(",", " ")
    return f"{sign}{dollars_str},{rest:02d} $"


def format_cad_en(cents: int) -> str:
    """English-Canadian receipt style: '$1,234.56'."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    dollars, rest = divmod(cents, 100)
    return f"{sign}${dollars:,}.{rest:02d}"
