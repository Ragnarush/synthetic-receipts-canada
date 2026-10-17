# Template `grocery_chain` — large grocery chain (Québec)

**Source.** Observation of real receipts from a large Québec grocery chain, printed in 2026
at two stores, paid in cash, debit, credit and split payment, at staffed checkouts and
self-checkouts. **Only the structure is reused**: block order, vocabulary, alignment, tax
codes. No receipt, no merchant name, no real number or name enters this repository.

A grocery store is not subject to mandatory billing (WEB-SRM): no QR code and no Revenu
Québec transaction number. The receipt is printed in capitals **without accents** (except
the terminal card slip, see below).

**Paper.** Thermal 80 mm (42 columns). On 58 mm, each item takes two lines.

| Block | Observed form | In the ground truth |
|---|---|---|
| Logo | the chain's banner | `merchant.name` (here the fictitious name, double height) |
| Header, form A | `ENSEIGNE VILLE (1234)` then `123,RUE, VILLE` | `merchant.name`, `merchant.address_lines`, `store_number` |
| Header, form B | `ENSEIGNE VILLE` then `819-555-0142` | `merchant.phone` |
| Department | `21-EPICERIE`, `35-CHARCUTERIE`… in bold | `items[].department` |
| Taxable item | `  01234567890    BISCUITS CHOCO` / `        FPMRJ` / amount **at the right edge** | `items[]` |
| Non-taxable item | `  01234567891    FROMAGE 600G   MRJ    15.00`: codes and amount **on the same line, amount in the middle column** | `items[]` |
| Quantity | `(2)` prefix before the code, then `2 @ $4.00` and the amount at the right edge | `items[].qty`, `unit_price_cents` |
| Promo price | `$1.75 lmt 6, $2.50 ch` then `2 @ $1.75 ch` | `items[].promo` |
| By weight | 4-digit PLU code, then `0.740 kg @ $4.39/kg` and the amount | `items[].weight_kg`, `unit_price_cents` (per kg) |
| Deposit | `  CONSIGNE 1` then amount, or `2@$0.60` on the next line | `items[]` with `kind: deposit` |
| Free item | `(6)12345  TIMBRE …` / `6 @ $0.00` / `0.00` | `items[]`, amount 0 |
| Subtotal | `SOUS-TOTAL   24.62`, double height | `subtotal_cents` |
| GST (TPS) | `F=T.P.S 5%   12.00 @  5.000%` then the amount at the right edge | `taxes[GST]`: `base_cents`, `cents` |
| QST (TVQ) | `P=TVQ 9.975% 12.00 @  9.975%` then the amount | `taxes[QST]`: `base_cents`, `cents` |
| Total | `TOTAL   26.42`, double height | `total_cents` |
| Item count (sometimes) | `NOMBRE D'ARTICLES:     12` | — |
| Cash | `COMPTANT 30.00` / `ARRONDI 0.02 (26.40)` / `MONNAIE 3.60` (double height) | `tenders[]`, `cash_rounding_cents`, `change_cents` |
| Card | terminal card slip **embedded**, then `DEBIT 12.34` or `CREDIT 12.34` | `tenders[]`, `card` |
| Loyalty | centred paragraph: `VOUS AURIEZ PU RECOLTER AU MOINS 1,230 POINTS …` | — |
| Registrations | `TPS # 12345-6789 RT0001`; `TVQ# 1234567890 TQ 0002` **sometimes absent** | `gst_number`, `qst_number` (`null` if absent) |
| Management | `DIRECTEUR DU MAGASIN: PRÉNOM NOM`, sometimes the phone | — |
| Register | `****` then `2026/01/15   201   201   01 1234   10:20`; at self-checkout `26/01/15 LIBRE-SERV 1 9991 21 1234 10:20` | `datetime` |
| Survey | paragraph + `CODE: 011526 102001 1234 01234` | — |

**Per-item tax codes.** `F` = GST, `P` = QST; the other letters (`M`, `R`, `J`, `Q`) are
specific to the chain and do not affect tax. Observed combinations: `FPMRJ` (both taxes),
`FMRJ` (GST only), `MRJ` and `RQ` (zero-rated). The GST and QST bases can therefore
**differ**. Deposits are not taxed.

**Cash rounding.** The total is paid rounded to the nearest 5 ¢. `ARRONDI` gives the
difference as an absolute value, and the amount in parentheses is the rounded total (the
amount deducted). When the customer pays the exact amount, there is no `MONNAIE` line.

**Embedded terminal card slip.** Between the total and the loyalty paragraph:

```
Type de Trans.:  ACHAT
Compte:  DEFAUT              12,34 CAD$
Type de carte:  D BIT
Num,ro de Carte:  ************0000 P
DateTime:        26/01/15 10:20:30
# de Ref.:       0010012345
# d'Autor.:      A1B2C3
Interac
A0000002771010 8000008000
      00/001 APPROUVEE - MERCI
      Conservez cette copie pour v,rification
           de votre rapport financier
          *** COPIE DU CLIENT ***
```

On half of the observed receipts, the `É` is replaced by a comma or a space (`Num,ro`,
`v,rification`, `D BIT`). This is an encoding error in the terminal, and the generator
reproduces it. The amount there uses a **decimal comma** (`12,34 CAD$`) while the rest of
the receipt uses a decimal point.

**Traps for an extractor.**
- **Two columns of amounts**: the middle column (non-taxable item on one line) and the
  right edge.
- **Three decoy amounts on every tax line**: the base (`75.40`), the rate (`5.000%`) and
  only then the tax.
- **Four date formats on the same receipt**: `2026/01/15` (register footer), `26/01/15` as
  *YY/MM/DD* (card slip, and footer at self-checkout) and `011526` as *MMDDYY* (survey
  code).
- The **rounded amount in parentheses** is not the total.
- The **points count** (`1,230`) has a thousands comma.
- The word `TOTAL` inside `SOUS-TOTAL`, and `DEBIT`/`CREDIT` repeating the amount paid.
- A **person's** name (store management) in the footer, far from the merchant name.

**Generated variation.** Banner and store, header A or B, 2 to 22 items from 3 to 8
departments, quantities, promos, items by weight, deposits, free stamps, cash payment
(with or without change), debit, credit or split, card slip with or without the encoding
error, QST printed or not, staffed checkout or self-checkout, item count.

**Out of template (not yet observed).** Coupons and discounts as negative lines, returns,
points redeemed for a discount, bags.
