"""The 'RELEVE DE TRANSACTION' card slip, as one widespread Canadian payment terminal prints it.

Observed identical at two different Québec retailers, printed either inside the sales receipt or
as a separate ticket. Amounts use a decimal point ('42.90 $') even when the receipt around it
uses a decimal comma, and the date is YY/MM/DD.
"""

import random
from datetime import datetime, timedelta

from ..layout import Align, Receipt

INTERAC_AID = "A0000002771010"


def releve_slip(r: Receipt, rng: random.Random, cents: int, when: datetime, invoice: str,
                last4: str | None = None) -> dict:
    """Interac debit, the only kind observed. Returns the card fields of the ground truth.

    `last4`: the card's digits when the receipt already printed them above the slip.
    """
    account = rng.choice(["CHEQUE", "CHEQUE", "DEFAUT FLASH"])  # FLASH = contactless tap
    if last4 is None:
        last4 = f"{rng.randint(0, 9999):04d}"
    at = when + timedelta(seconds=rng.randint(5, 50))
    ref = f"00{rng.randint(10_000_000, 19_999_999)} {rng.choice('CH')}"
    auth = "".join(rng.choice("0123456789ABCDEF") for _ in range(6))
    dashes = "-" * 11
    pad = r.columns - 16
    r.add()
    r.add("        RELEVE DE TRANSACTION")
    r.add()
    r.add("TYPE: ACHAT")
    r.add()
    r.add(f"COMPTE: : {account}")
    r.add(dashes.rjust(pad))
    r.add(f"MONTANT:{f'{cents // 100}.{cents % 100:02d} $':>{pad - 8}}")
    r.add(dashes.rjust(pad))
    r.add("Type de carte: Interac")
    r.add()
    r.add(f"NUMERO CARTE:    {'*' * 12}{last4}")
    r.add(f"DATE/HEURE:      {at:%y/%m/%d %H:%M:%S}")
    r.add(f"NUMERO REF:      {ref}")
    r.add(f"AUTOR #:         {auth}")
    r.add(f"NUMERO DE FACT:  {invoice}")
    r.add()
    r.add("Interac")
    r.add(INTERAC_AID)
    r.add(rng.choice(["0080008000  EC00", "8080008000", "8000008000  7800"]))
    r.add()
    r.add("00/001  APPROUVEE - MERCI", align=Align.CENTER)
    r.add()
    r.add("-- IMPORTANT --", align=Align.CENTER)
    r.add("Conserver cette copie pour vos dossiers", align=Align.CENTER)
    r.add()
    r.add("*** COPIE DU CLIENT ***", align=Align.CENTER)
    return {"network": "Interac", "masked_number": f"{'*' * 12}{last4}", "account": account,
            "datetime": at.isoformat(), "reference": ref, "authorization": auth}
