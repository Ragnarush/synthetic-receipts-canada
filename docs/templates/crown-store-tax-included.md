# Template `crown_store_tax_included` — crown corporation store, taxes included (Québec)

**Source.** Observation of real receipts from two Québec retail crown corporations
(alcohol, cannabis), printed in 2026, paid in cash, debit and split payment, including
reprints. **Only the structure is reused**; merchant names, addresses and numbers are
fictitious, and so are the examples below.

Two variants, `alcohol` and `cannabis`, share the essentials: **displayed prices include
taxes**. There is no printed subtotal, and the GST (TPS) and QST (TVQ) lines carry
`(incl.)`: they are **already in the total**.

**Paper.** Thermal 80 mm (42 columns); on 58 mm, long lines wrap.

| Block | `alcohol` variant | `cannabis` variant | Ground truth |
|---|---|---|---|
| Logo | banner | banner | `merchant.name` (fictitious name, double height) |
| Address | `123, rue X - Ville` / `Ville, QC A1B 2C3` / `819-555-0123` | `123, rue X` / `Ville, QC A1B 2C3` / `Canada` / `8445550123` (10 digits run together) | `merchant` |
| Transaction | `Billet : 12345    Caisse : 1` | `Transaction : 12345  Caisse 2` | `transaction_number` |
| Store | `Succursale : 12345  Caissier : 1234567` | `Magasin : 12345  Caissier : 123456` | `store_number` |
| Date | `Date : 2026/01/15   Heure : 10:20` (*YYYY/MM/DD*) | `Date : 15/01/2026   Heure : 10:20` (*DD/MM/YYYY*) | `datetime` |
| Reprint | 5 lines of stars with `RÉIMPRESSION`, before the items and after the footer | — | `reprint` |
| Items | `Article  Qté  Prix  Montant`, then the name on one line and `code  1  37,50 $  37,50 $` on the next | same, `42,90$` without a space; a product bought twice prints twice | `items[]` |
| Total | `Total   37,50 $`, aligned on the Prix column | same | `total_cents` |
| Taxes | `123456789 RT0001 TPS (incl.)   1,63 $` | numbers printed with **8 digits** | `taxes[]` (`included: true`) |
| Payment | `Comptant 20,00 $` / `ACHAT DÉBIT 17,50 $` / `Remise Comptant 0,00 $` | `Comptant 90,00$` then `Monnaie` / `Comptant (4,20)$`; or `Debit Card` + full embedded card slip | `tenders[]`, `change_cents`, `card` |
| Notice | `Taxe spécifique sur les boissons alcooliques incluse` | pointer to information on consumption | — |
| Counters | `Nombre d'articles vendus = 1` | same + `Poids total Articles vendus =  7g` | `declared_weight_g` |
| Footer | barcode + alphanumeric code `T…` (22 characters), `Copie client` | same, `Exemplaire client` | — |

**Computing included taxes.** For a tax-included price P: GST = P × 5 / 114.975 and
QST = P × 9.975 / 114.975, rounded to the cent (half up). Both variants confirm this to
the cent. `subtotal_cents` in the ground truth equals total − GST − QST: **it is not
printed**; it is what an extractor has to recompute.

**Embedded card slip (cannabis, debit).** A summary (`Debit Card`, masked card,
`Numéro d'autorisation`, `Type de transaction : Vente`, `Heure d'autorisation`, terminal
version line) then the full `RELEVE DE TRANSACTION` card slip. This card slip is identical
from one retailer to the next (`families/_terminal.py`). It gives `MONTANT: 42.90 $` with a
**decimal point**, while the rest of the receipt uses a comma, and the date as *YY/MM/DD*
(`26/01/15 10:20:45`). On the alcohol side, the card slip comes out on a separate ticket;
it belongs to the "terminal card slip" family.

**Declared weight (cannabis).** `Poids total Articles vendus` is the **dried-cannabis
equivalent** under federal regulations: 1 g of hashish or resin counts as 4 g. A 3.5 g
pouch of hashish therefore prints `14g`. The total stays under the 30 g possession limit.
It is a decoy number for an extractor, not an amount.

**Traps for an extractor.**
- **Adding the taxes to the total counts them twice**: `(incl.)` is the only clue.
- No `SOUS-TOTAL`: an extractor that requires one finds nothing; an extractor that takes
  the first sum after the items takes the total.
- Each tax line **starts with the registration number** (8 to 10 digits).
- The change given is **negative, in parentheses**, under a second `Comptant`.
- Split payment: `Comptant` and `ACHAT DÉBIT` are two partial amounts.
- Three date formats depending on the variant and the card slip.
- `Caissier : 1234567` and the terminal version line look like amounts.

**Generated variation.** Variant, banner, store, 1 to 5 items (duplicates included), cash
(with or without change), debit, split (alcohol only), reprint (alcohol, 20 %).

**Out of template (not yet observed).** Credit card, returns, container deposit,
discounts.
