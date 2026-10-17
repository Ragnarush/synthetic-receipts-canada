import os
import random
from functools import cache

from synthetic_receipts_canada.families import FAMILIES

# Receipts checked per family and paper width; raise it to hunt rare draws: RECEIPTS_COUNT=5000.
COUNT = int(os.environ.get("RECEIPTS_COUNT", 200))
PAPERS = (58, 80)


@cache
def sample(family: str, paper_mm: int, seed: str = "1") -> tuple:
    """Receipts drawn exactly as the CLI draws them, without rendering an image."""
    module = FAMILIES[family]
    return tuple(module.generate(random.Random(f"{seed}/{family}/{index}"), paper_mm=paper_mm)
                 for index in range(1, COUNT + 1))
