# synthetic-receipts-canada

A generator of synthetic Canadian receipts (Québec first), with the ground truth of each
receipt, for testing an OCR engine or a field extractor without handling a single real
receipt. Public overview: `README.md`. This file is for anyone changing the repository,
human or coding agent: first what is not negotiable, then how to work.

## Absolute rule: no real data

This repository is **public**. A template describes a **structure** (block order,
vocabulary, alignment, tax codes), never a specific receipt.

- No real receipt is committed, not even anonymized, not even a cropped photo. Source
  photos stay **outside the repository** and are never copied into it, even temporarily.
- No brand, branch, address, customer city, person's or pet's name, GST/QST number, card
  number (including the last 4 digits), cashier, reference or authorization number taken
  from a real receipt. **Not in the code, not in the template sheets in `docs/templates/`,
  not in `README.md`, not in commit messages.**
- **An example is invented, never copied**: `12345-6789 RT0001`, `************0000`,
  `819-555-0142`, `07/11/26`, `37.50 $`. Never reuse an amount, a date or a time from a
  source receipt "to illustrate": it is the most frequent leak (an amount copied into a
  sheet, then into the README; a date copied from working notes).
- Sheets do not name the observed brand: "a large Québec grocery chain", "two crown
  corporations", "a convenience store".
- A commit message does not describe the source either: no "the sample landed on the same
  city as the real receipt".
- A random draw can land on a real value (the city and date of an observed invoice, for
  example). Rule it out with a **general rule** (bound a family's dates), never by writing
  the real value into the code to exclude it: that would publish it.

**Check before every commit of a family drawn from observation**: reread the sheet line by
line, then search (`grep`) the source receipts' values in the diff, the README and the
generated corpus. **Check before every push**: the same `grep` over **every commit**
(`git log -p origin/main..HEAD`) and over the messages (`git log --format=%B`), not only
the final state, since a value added then removed stays readable in history. If a leak is
in an unpushed commit, fix that commit (`git commit --fixup`, then
`git rebase --autosquash`); do not add a corrective commit on top. Several leaks have been
caught this way: last 4 card digits, a cashier number, amounts and dates reused as
examples.

The guardrails against use as fake receipts live **in the code** and are not relaxed:
fictitious merchants assembled from pieces (`fakes.py`), phones in the 555-01XX block,
GST/QST numbers that **fail** the Luhn check, a "SPÉCIMEN" line on every receipt, a QR code
pointing to this repository, URLs on `.example`, placeholder surnames (`Doh`, `Untel`…).

## Fidelity to observation

A generator only produces what has been **observed**. Everything else goes in the sheet's
"Out of template (not yet observed)" section, until a receipt shows it.

- An unobserved form is not invented "for variety": one account type seen, one account
  type generated.
- An unavoidable extrapolation (the other months when only `sept.` was seen) is
  **flagged as such** in the sheet.
- A known rule applies even when the observed receipt does not show it, but an accident of
  the sample is not a rule. Two cash receipts happened to have totals that were multiples
  of 5 cents: that is not a constraint. The rule is that only a cash payment rounds to
  5 cents (`money.cash_rounded`, Canada-wide since the cent was withdrawn in 2013), the
  total keeps its cents, and the difference goes to `cash_rounding_cents`, printed or not.
- A terminal that always prints on its own paper (58 mm) does so whatever `--paper` says:
  the family writes the real width in `paper_width_mm`, and the CLI renders the image at
  that width.

## Conventions

- **Everything in the repository is in English**: code, comments, template sheets, README,
  this file, commit messages. Text printed on a receipt stays as printed (French on a
  Québec receipt), in backticks in the sheets. Comments only for the non-obvious *why*.
- Commits go straight to `main`, with detailed messages. **Pushing happens only on
  explicit request**: pushing is publishing.
- Stage named files, never `git add -A` or `commit -a`.
- Money in **integer cents**, rounded half up (`money.py`), never `float`.

### Ground truth

- `null` means "absent from the receipt", never a default value. A card slip does not
  print the purchase total: its `total_cents` is `null`, not the amount debited.
- Common keys: `schema_version`, `family`, `country`, `province`, `currency`, `language`,
  `paper_width_mm`, `merchant`, `datetime`, `transaction_number`, `items`,
  `subtotal_cents`, `taxes`, `total_cents`, `tip_cents`, `gst_number`, `qst_number`,
  `payment_method`, `document_kind`, `text_lines`. The CLI adds `files` and `degradation`.
- `document_kind`: `sales_receipt`, `original_invoice`, `closing_receipt`,
  `payment_slip`, `invoice`. Add one only for a document of a different nature.
- `datetime` in ISO format, at the printed precision: to the minute if the receipt prints
  `10:20`, a date only if no time is printed.
- A family with several variants writes `variant` and draws the variant **first**.
- A value that is not printed but follows from the printed ones (an unprinted subtotal, an
  unprinted cash rounding) may be given, and its sheet says it must be recomputed.
- Family-specific fields (`card`, `client`, `patient`, `associate_id`…) are described in
  the family's sheet and in the format section of `README.md`.
- `text_lines` is the exact printed text: it is what the checks verify, and what an
  extractor receives when it skips OCR.

## Layout

```
src/synthetic_receipts_canada/
  cli.py        generate: one RNG per receipt, seeded by (seed, family, index)
  layout.py     Receipt = text lines in fixed columns (42 on 80 mm, 32 on 58 mm),
                QR, barcode, wrap_overflow()
  render.py     thermal-print image rendering (Pillow)
  degrade.py    "phone photo" degradation
  fakes.py      fictitious merchants, addresses, people, numbers
  money.py      cents, rounding, cash rounding, fr/en formats
  families/     one module per family: generate(rng, paper_mm) -> (Receipt, ground truth),
                listed in families/__init__.py
    _websrm.py       blocks prescribed by Québec mandatory billing (Revenu Québec)
    _terminal.py     shared "RELEVE DE TRANSACTION" card slip
    _crown_store.py  crown-store header and products, shared by two families
docs/templates/ one template sheet per family (source, block table, traps, variation)
docs/sources/   official documents the WEB-SRM templates are drawn from (in French)
corpus/         sample of 20 receipts per family (seed 1), committed
```

## Adding a family (or a variant)

1. **Sheet first** (`docs/templates/<family>.md`, modeled on `grocery-chain.md`): source,
   table of block → observed form → ground-truth field, traps for an extractor, generated
   variation, what is out of template (not observed). Get it reviewed before writing code.
   If the receipt shows the same kind of document as an existing family, from another
   device or another store, it is a **variant** of that family.
2. Module `families/<family>.py`, registered in `families/__init__.py`. Reuse
   `_terminal.py`, `_websrm.py` and `_crown_store.py` rather than copying; what serves two
   families moves to `layout.py` or a shared `_module`. Such a move must change **neither
   the order nor the number** of random draws.
3. Check, on at least 200 receipts at 80 mm **and** 200 at 58 mm:
   - the arithmetic: item sum, taxes to the cent, payments = total + rounding + change;
   - that the amounts, dates and numbers printed in `text_lines` match the ground truth;
   - that no line of `text_lines` exceeds the paper width;
   - the guardrails: Luhn failing, 555-01XX, SPÉCIMEN line, placeholder names.

   There is no test suite yet: these checks are written for the family and run with
   `uv run python -I`.
4. Look at at least one clean and one degraded image, at 80 and at 58 mm.
5. **No regression**: regenerate `--family all --count 20 --seed 1` into a temporary
   folder and check that existing families are **byte-for-byte identical** to `corpus/`
   (`diff -rq`). Any draw added on a shared path shifts existing receipts. Adding a variant
   shifts its family's sample: fine while that sample is unpublished, to be stated in the
   commit otherwise.
6. Copy the new family's sample into `corpus/`, add its row to the families table in
   `README.md` (and its own fields to the format section).
7. Run the leak check before committing (see above), then commit naming the files.

## Commands

```sh
uv sync
uv run synthetic-receipts-canada generate --family all --count 20 --seed 1 --out /tmp/x
diff -rq /tmp/x corpus     # no regression: only new families differ
uv run synthetic-receipts-canada generate --family grocery_chain --count 200 --paper 58 --no-degrade --out /tmp/y
git log -p origin/main..HEAD | grep -nE '<values from the source receipts>'   # before a push
```

Python run on files from outside the repository: `uv run python -I`.
