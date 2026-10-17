# Template `big_box_retail` — office-supply and electronics big-box store (Québec)

**Source.** Observation of one real receipt from a large office-supply and electronics
chain, printed in Québec in 2026, paid in cash. **Only the structure is reused**; banner,
address, numbers and items are fictitious, and so are the examples below.

**Paper.** Thermal 80 mm (42 columns); on 58 mm, long lines wrap.

| Block | Observed form | Ground truth |
|---|---|---|
| Banner | chain name, centred, normal size | `merchant.name` |
| Store | the city name alone, centred | — |
| Address | `12 Rue-des-Fictifs St` (**English form**, street type last) / `Ville, QC A1B 2C3` / `819-555-0123` | `merchant.address_lines`, `merchant.phone` |
| Transaction | `VENTE` on the left; on the right `00012 001 004 12345` (four groups, the last one is the transaction number) | `transaction_number` |
| Date | on the right `0042 15/01/26 10:20`: store number, then *DD/MM/YY* and the time | `store_number`, `datetime` |
| Associate | `1234567` alone on its line, unlabelled | `associate_id` |
| Item | `1    Clavier sans fil Doh`: quantity, then abbreviated description | `items[].qty`, `items[].description` |
| Code | `     012345678905              49.99B`: 12-digit UPC, price with a **decimal point** followed by the tax code `B` | `items[].upc`, `items[].line_total_cents`, `items[].tax_flags` |
| Eco fee | `     UGS 123456 d'écofrais inclus` under electronic items: UGS (SKU) number, and the eco fee (écofrais) is **included in the price** | `items[].sku`, `items[].eco_fee_included` |
| Subtotal | `Total partiel   49,99` (**decimal comma**) | `subtotal_cents` |
| Taxes | `     5.00% TPS   2,50` / `     9.975% TVQ   4,99` (rate with a point, amount with a comma) | `taxes[]` |
| Total | `Total   57,48 $` | `total_cents` |
| Payment | `Comptant   60,00` / `Comptant Rendu   2,50` (given back on the total rounded to `57,50`) | `tenders[]`, `change_cents`, `cash_rounding_cents` |
| Notices | two star-framed boxes: non-returnable products, device trade-in programme | — |
| Thanks | `Merci d'avoir magasiné chez <enseigne>` | — |
| Registrations | `TPS : 123456789 - TVQ : 1234567890TQ0001AB` on one line | `gst_number`, `qst_number` |
| Survey | contest invitation, **QR code**, `textez XYZ42 au 12345`, `ou visitez <site>/survey/42`, legal notices, address of the contest rules | — |
| Barcode | barcode with its digits spaced out: store + date *DDMMYY* + transaction + register | — |

**Three ways of writing numbers on one receipt.** The item price uses a point
(`49.99B`), totals use a comma (`49,99`), rates use a point with `%` (`9.975%`).

**Taxes.** GST (TPS) 5 % and QST (TVQ) 9.975 % on the subtotal, rounded to the cent (half
up). The eco fee is already in the price and is therefore taxed.

**Cash.** Since the cent was withdrawn (2013), only the **cash payment** rounds to the
nearest 5 ¢ (x.x1–x.x2 down, x.x3–x.x4 up…); the printed total keeps its cents. The
observed receipt had a total that was already a multiple of 5 ¢; when it is not, the
change is given on the rounded total, **with no rounding line printed** (form not
observed, deduced from the rule). The difference lives in `cash_rounding_cents`, to be
recomputed.

**Traps for an extractor.**
- `B` glued to the price (`49.99B`): it must be stripped without losing the amount.
- The GST number is printed **without** `RT0001` (9 digits alone), and the QST number
  carries two extra letters after `TQ0001`.
- `Total partiel` then `Total`: an extractor that takes the first match for "Total" gets
  the subtotal.
- `Comptant Rendu` is the change, not a payment.
- `Comptant` − `Comptant Rendu` ≠ `Total` as soon as the total does not end in 0 or 5: the
  difference is the rounding, which nothing prints.
- *DD/MM/YY* (`07/11/26`), preceded by the store number (`0042`), which can be read as a
  time or an amount.
- Unlabelled runs of digits: the group `00012 001 004 12345`, the associate `1234567`, the
  UPC, the UGS, the digits under the barcode.
- The contest prize (`500 $`) is an amount inside the promotional text.

**Generated variation.** Banner, city, address, 1 to 5 office-supply and electronics items
(eco fee on electronics only), amount tendered (next bill up or exact amount), presence of
the notice boxes.

**Out of template (not yet observed).** Card payment (slip inline or not), printed
rounding line, quantity above 1, discounts and reduced prices, returns, non-taxable item
(tax code other than `B`), loyalty programme.
