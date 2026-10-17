"""One module per receipt family. Each exposes `generate(rng, options) -> (Receipt, ground_truth)`."""

from . import grocery_chain, restaurant_websrm, taxi_websrm

FAMILIES = {
    "restaurant_websrm": restaurant_websrm,
    "taxi_websrm": taxi_websrm,
    "grocery_chain": grocery_chain,
}
