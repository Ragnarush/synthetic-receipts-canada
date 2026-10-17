"""One module per receipt family. Each exposes `generate(rng, options) -> (Receipt, ground_truth)`."""

from . import (big_box_retail, crown_store_tax_included, grocery_chain, payment_terminal_slip, professional_invoice,
               restaurant_websrm, taxi_websrm)

FAMILIES = {
    "restaurant_websrm": restaurant_websrm,
    "taxi_websrm": taxi_websrm,
    "grocery_chain": grocery_chain,
    "crown_store_tax_included": crown_store_tax_included,
    "payment_terminal_slip": payment_terminal_slip,
    "big_box_retail": big_box_retail,
    "professional_invoice": professional_invoice,
}
