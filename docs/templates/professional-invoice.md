# Template `professional_invoice` — veterinary clinic invoice (Québec)

**Source.** Observation of one real invoice from a Québec veterinary clinic, printed in
2026 on a thermal ticket, paid in cash. **Only the structure is reused**; clinic, client,
animal, numbers and products are fictitious, and so are the examples below. The real
invoice carries the client's name and address and the name of their animal: none of it is
reused, not even the form of the animal's name.

An invoice for professional services differs from a store receipt: it names the
**client** (with their address and file number) and the **patient**, and carries **no
time**.

**Paper.** Thermal 80 mm. The original prints in small characters (about 56 columns); the
generator stays at 42 columns and wraps long lines.

| Block | Observed form | Ground truth |
|---|---|---|
| Clinic | `Clinique` / `vétérinaire` / `Doh inc`, large, centred, over three lines | `merchant.name` |
| Address | `123 avenue des Fictifs` / `Ville, QC A1B 2C3` | `merchant.address_lines` |
| Phone | `Téléphone:  (819)555-0142` (area code in parentheses, no space after) | `merchant.phone` |
| Registrations | `TPS: 123456789  TVQ: 1234567890`: **without** `RT0001` or `TQ0001` | `gst_number`, `qst_number` |
| Invoice | `Facture: 123456` | `transaction_number` |
| Date | `Date: 7-nov.-2026`: *D-abbreviated month.-YYYY*, **no time** | `datetime` (date only) |
| Client | `M. Jean Untel (12345)` (title, name, file number) / address / `Ville, QC  A1B 2C3` (two spaces before the postal code) | `client.name`, `client.id`, `client.address_lines` |
| Patient | `Biscuit - 12345` (animal's name, patient number) | `patient.name`, `patient.id` |
| Item | `   1 Antiparasitaire DOH canin 10.1 kg à      43,01 $`: quantity, description, amount on the right; the description wraps to the next line, indented | `items[]` |
| Subtotal | `Sous-total:   43,01 $`, right-aligned block | `subtotal_cents` |
| Taxes | `TPS(5%):   2,15 $` / `TVQ(9,975%):   4,29 $` (rate with a **comma**) | `taxes[]` |
| Total | `Total:   49,45 $` | `total_cents` |
| Payment | `7-nov.-2026  Comptant:   50,00 $`: the payment date **repeated** before the method | `tenders[]` |
| Change | `Monnaie   0,55 $` (no colon), given on the total rounded to 5 ¢ | `change_cents`, `cash_rounding_cents` |
| Balance | `Solde:   0,00 $` | `balance_cents` |
| Notices | `AUCUN RETOUR SUR LES MEDICAMENTS…` in capitals, prescription fees included in the price, interest on unpaid balances (`2% par mois`, `24%` per year) | — |

**Taxes.** GST (TPS) 5 % and QST (TVQ) 9.975 % on the subtotal, rounded to the cent (half
up).

**Cash.** Since the cent was withdrawn (2013), only the **cash payment** rounds to the
nearest 5 ¢ (x.x1–x.x2 down, x.x3–x.x4 up…); the printed total keeps its cents. The
observed invoice had a total that was already a multiple of 5 ¢; when it is not, the
change is given on the rounded total, **with no rounding line printed** (form not
observed, deduced from the rule). The difference lives in `cash_rounding_cents`, to be
recomputed.

**Abbreviated months.** Only `sept.` was observed. The other months follow the usual French
abbreviations (`janv.`, `févr.`, `mars`, `avr.`, `mai`, `juin`, `juil.`, `août`, `sept.`,
`oct.`, `nov.`, `déc.`): this is an extrapolation, flagged as such.

**Traps for an extractor.**
- `7-nov.-2026`: no month digits and no slashes; the abbreviated month ends with a point
  glued to the hyphen.
- Numbers inside the description (`10.1 kg à 20kg`, with a **point**) while amounts use a
  comma; they are not prices.
- Three numbers in parentheses or after a hyphen: client file, patient, phone area code.
- Bare GST and QST numbers, with no suffix: only the label tells them apart from other
  numbers.
- `Monnaie` then `Solde: 0,00 $`: two amounts after the total that are not payments; a
  zero `Solde` does not mean "free".
- `Comptant` − `Monnaie` ≠ `Total` when the total does not end in 0 or 5: the rounding is
  not printed, and the balance stays at zero.
- `2%` and `24%` in the interest notice look like tax rates.
- The client's name is not the merchant: the first proper name after the header is the
  client's.

**Generated variation.** Clinic, client (placeholder names), animal (invented names, dog or
cat), 1 to 4 lines (exam, vaccine, medication with a weight band, food), amount tendered,
presence of the notices. Dates in 2024 and 2025 only: no generated invoice falls in the
year the source invoice was printed.

**Out of template (not yet observed).** Card, partial payment with a balance due, several
animals on one invoice, non-taxable item, discounts, other professions (dentist,
physiotherapist…), invoice on letter paper.
