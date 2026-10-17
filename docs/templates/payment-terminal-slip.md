# Template `payment_terminal_slip` — terminal card slip on a separate ticket (Québec)

**Source.** Observation of three real tickets printed in 2026: two from a Québec alcohol
crown corporation (one of them a reprint) and one from a convenience store. The payment
terminal prints on a **separate ticket** there, whereas other retailers include it in the
sales receipt (see `grocery-chain.md`, `crown-store-tax-included.md`). **Only the structure
is reused**; banners, addresses and numbers are fictitious, and so are the examples below.

The ticket carries **no items, no taxes and no purchase total**: only the merchant header
and the card slip. It is a document in its own right that an extractor often receives on
its own (a photo of the "wrong" ticket, or the only paper a small shop hands over).

Two variants, printed by two different terminals:

- `store_header`: the store's till prints its header, then the `RELEVE DE TRANSACTION`
  card slip (crown corporation);
- `standalone_terminal`: a standalone terminal, with no till attached, prints everything
  itself (convenience store).

## Variant `store_header`

**Paper.** Thermal 80 mm (42 columns); on 58 mm, long lines wrap.

| Block | Observed form | Ground truth |
|---|---|---|
| Logo | banner | `merchant.name` (fictitious name, double height) |
| Address | `123, rue X - Ville` / `Ville, QC A1B 2C3` / `819-555-0123` | `merchant` |
| Transaction | `Billet : 12345    Caisse : 1` | `transaction_number` |
| Branch | `Succursale : 12345  Caissier : 1234567` | `store_number` |
| Date | `Date : 2026/01/15   Heure : 10:20` (*YYYY/MM/DD*) | `datetime` |
| Reprint | 5 lines of stars with `RÉIMPRESSION`, **once only**, before the card slip | `reprint` |
| Title | `RELEVE DE TRANSACTION` | — |
| Type | `TYPE: ACHAT` | — |
| Account | `COMPTE: : CHEQUE` or `COMPTE: : DEFAUT FLASH` (double colon as printed) | `card.account` |
| Amount | `MONTANT:          37.50 $` between two rules, **decimal point** | `tenders[0].cents`, `card` |
| Card | `Type de carte: Interac`, `NUMERO CARTE:    ************0000` | `card.network`, `card.masked_number` |
| Timestamp | `DATE/HEURE:      26/01/15 10:20:45` (*YY/MM/DD*, to the second) | `card.datetime` |
| References | `NUMERO REF:      0012345678 C`, `AUTOR #:         1A2B3C` | `card.reference`, `card.authorization` |
| Invoice | `NUMERO DE FACT:  12345` = the `Billet` number | `transaction_number` |
| Application | `Interac` / `A0000002771010` / terminal verification line | — |
| Result | `00/001  APPROUVEE - MERCI`, `-- IMPORTANT --`, `Conserver cette copie…`, `*** COPIE DU CLIENT ***` | — |

The card slip is the one in `families/_terminal.py`, reused unchanged: it is identical on
both tickets and on the receipts that include it.

**Amount ≠ purchase total.** On the ticket observed with a split payment, `MONTANT` is only
the share paid by debit; the cash share appears only on the sales receipt. In the ground
truth, `total_cents` is therefore **`null`** (absent from the ticket) and the debited
amount lives in `tenders` and `card`.

**Two times.** `Heure : 10:20` in the header (to the minute) and `DATE/HEURE:` in the card
slip (to the second, a few tens of seconds later, sometimes the next minute). The ground
truth keeps the header in `datetime` and the card slip in `card.datetime`.

## Variant `standalone_terminal`

**Paper.** Narrow terminal ticket, 58 mm (32 columns). Bold characters, `VENTE DEBIT` and
the amount line printed large; the footer in small condensed characters.

| Block | Observed form | Ground truth |
|---|---|---|
| Merchant | abbreviated name in capitals (`DEP GEN DOH ST-QUIDAM`), centred | `merchant.name` |
| Address | `123 CHEMIN DU` / `QUIDAM` (wrapped at a word) / `VILLE, QC A1B2C3` (postal code **without a space**) | `merchant.address_lines` |
| Phone | `8195550142` (10 digits run together) | `merchant.phone` |
| Title | `VENTE DEBIT`, bold, large | — |
| Merchant ID | `IDM: 1234567` (merchant identifier) | `card.merchant_id` |
| Terminal | `IDT: 001` on the left, `No. REF: 00000042` on the right | `card.terminal_id`, `card.reference` |
| Batch | `No Lot: 123001` on the left, `NRE: 00000042` on the right (= `No. REF`) | `card.batch` |
| Timestamp | `01/15/26` on the left, `10:20:45` on the right: **MM/DD/YY** | `datetime`, `card.datetime` |
| Authorization | `CODE APPR: 1A2B3C` | `card.authorization` |
| Trace | `No Trace: 00123456` | `card.trace` |
| Account | `DEBIT/PAR DEFAUT` on the left, `Sans Contact` on the right | `card.account`, `card.entry` |
| Card | `************0000` alone on its line | `card.masked_number` |
| Amount | `MONTANT` on the left, `$12.50` on the right, bold, large: **sign first**, decimal point | `tenders[0].cents` |
| Result | `APPROUVE`, centred | — |
| Application | `Interac` / `AID: A0000002771010` / `TVR: 80 00 00 80 00` (spaced bytes) | `card.network` |
| Notice | `VOTRE COMPTE SERA DEBITE DU` / `MONTANT CI-DESSUS` / `VEUILLEZ CONSERVER CETTE COPIE` / `POUR LA VERIFICATION DU RELEVE`, condensed | — |
| Footer | `THANK YOU! / MERCI!`, `COPIE CLIENT` | — |

Only one time on the ticket: `datetime` and `card.datetime` hold the same value, to the
second. No till transaction number: `transaction_number` and `store_number` are `null`.

## Traps for an extractor (both variants)

- Taking `MONTANT` for the purchase total: true only if everything was paid by card.
- No taxes, no GST (TPS) or QST (TVQ) number: an extractor that requires them must return
  "absent", not zero.
- Two date formats on the same ticket (*YYYY/MM/DD* and *YY/MM/DD*); `26/01/15` reads just
  as well as *DD/MM/YY*.
- Decimal point (`37.50 $`) whereas the sales receipt for the same purchase uses a comma.
- `Caissier : 1234567`, `NUMERO REF`, `A0000002771010` and the verification line look like
  amounts or dates.
- `Billet` and `NUMERO DE FACT` repeat the same number: it is the key linking the ticket to
  the sales receipt.
- *MM/DD/YY* (`standalone_terminal`): `04/11/26` is April 11, not November 4. Seventh date
  format in the corpus, the only one that puts the month first.
- `$12.50`: sign before the number, English style, on a French ticket.
- `No. REF` and `NRE` repeat the same zero-padded number; `IDM`, `No Lot`, `No Trace` and
  the run-together phone are all digit runs with no amount label.
- `TVR: 80 00 00 80 00` looks like a line of amounts.

**Generated variation.** Variant (half and half). `store_header`: banner, branch, account
(`CHEQUE` / `DEFAUT FLASH`), amount (full payment or debit share of a split payment),
reprint (20 %), 80 and 58 mm. `standalone_terminal`: merchant, address (wrapped or not),
small convenience-store amount, batch and reference numbers; always 32 columns, even when
80 mm is requested, like the real terminal.

**Out of template (not yet observed).** Credit card, refund, declined transaction, merchant
copy, tip entered at the terminal, convenience-store sales receipt (only the card slip has
been observed).
