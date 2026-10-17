# Template `restaurant_websrm` — restaurant, bar, caterer (Québec)

**Source.** Revenu Québec, *Exemple de facture – Secteur de la restauration* (sample bill,
restaurant sector), under *facturation obligatoire* (mandatory billing) with a certified
sales recording system (*système d'enregistrement des ventes*, SEV) / MEV-WEB, image of
July 2025: `docs/sources/revenu-quebec-exemple-facture-restauration-2025-07.png`. The
official page numbers 20 elements; they are listed below in the same order. The elements
between the two runs of "=" are prescribed and ordered; before the first run and after the
second, the merchant may add whatever it wants (server name, thank-you note, survey, logo).

**Paper.** Thermal 80 mm (42 columns) most often; 58 mm (32 columns) exists. Fixed-pitch
font. The business name is often printed double height or replaced by a logo.

| # | Element | Observed form | In the ground truth |
|---|---|---|---|
| 1 | Name under which the business operates, full address of the establishment | centred, 2 to 3 lines | `merchant` |
| 2 | Time of transmission | `YYYY-MM-DD HH:MM:SS` | `datetime` |
| 3 | SEV transaction number | `TRANSACTION #123456` | `transaction_number` |
| 4 | Description of each good or service | `1 Spaghetti` + price | `items[]` |
| 5 | Taxes applicable per item | `FP` (federal, provincial), `FPS` (+ additional tax, alcohol) | `items[].tax_flags` |
| 6 | Subtotal before taxes | `SOUS-TOTAL   18,00 $` | `subtotal_cents` |
| 7 | GST (TPS) registration number | `TPS: 123456789   RT 0001` | `gst_number` |
| 8 | QST (TVQ) registration number | `TVQ: 1234567890  TQ 0001` | `qst_number` |
| 9 | Payment method (closing receipt only) | `CARTE DE DÉBIT`, `CARTE DE CRÉDIT`, `COMPTANT` | `payment_method` |
| 10 | Credit note only: customer name, refund date | *not generated in v1* | — |
| 11 | Run of `=` signs | full width | — |
| 12 | GST amount | `TPS:   0,90 $` | `taxes[kind=GST]` |
| 13 | QST amount | `TVQ:   1,80 $` | `taxes[kind=QST]` |
| 14 | Total of the supply (subtotal + GST + QST) | `TOTAL:  20,70 $`; tip separate, after it | `total_cents`, `tip_cents` |
| 15 | Statement depending on the situation | `PAIEMENT REÇU` or `FACTURE ORIGINALE` | `document_kind` |
| 16 | QR code with a web address | ~ half the width | `websrm.qr_url` (points to this repository) |
| 17 | Time of processing by Revenu Québec | `YYYY-MM-DD HH:MM:SS`, a few seconds after #2 | `websrm.processed_at` |
| 18 | Transaction number assigned by Revenu Québec | `ABCD-1234-EFGH-5678` | `websrm.transaction_id` |
| 19 | Unique device identifier | `0001-2345-6789` | `websrm.device_id` |
| 20 | Run of `=` signs | full width | — |

**Traps for an extractor.** Two "TPS/TVQ" blocks on the same receipt: the registration
numbers (7, 8) and the amounts (12, 13). The word `TOTAL` appears inside `SOUS-TOTAL`
before it appears alone. The tip follows the total without being part of it. The line
`Boiss.alc.(t.incl.)` holds a potential decoy amount ("t.incl."). The "SPÉCIMEN" footer
must be ignored.

**Generated variation.** Merchant, items (1 to 7, quantities), alcohol or not, closing
receipt (80 %) or original invoice, payment method, tip, server line, thank-you note,
phone (60 %; `merchant.phone` is `null` when it is not printed), narrow or full-width
amount columns. Dates start on 2025-06-01, the day MEV-WEB receipts became mandatory for
every restaurant: the source sample has the MEV-WEB form, earlier receipts did not.
