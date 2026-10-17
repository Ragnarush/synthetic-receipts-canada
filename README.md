# synthetic-receipts-canada

Synthetic Canadian receipts, Québec first, each with its ground truth. Built to test OCR
engines and receipt-field extractors (merchant, date, subtotal, GST, QST, total) without
handling a single real receipt.

## Why this project exists

Anyone building a receipt scanner, an expense app or a bookkeeping tool for Canada hits
the same wall: **there is no public dataset of Canadian receipts**. The known datasets
(SROIE, CORD) are Malaysian or Indonesian, in English, with no GST, QST, HST or PST. And a
real receipt is personal data: the last four digits of a card, a member number, a
customer's name, where and when someone shopped.

This repository solves both problems. Receipts are **generated** from templates that
reproduce the **structure** of real receipts (block order, vocabulary, alignment, tax
codes, the traps an extractor falls into), then filled with **verifiably fake data**.
Every receipt ships with the exact answer an extractor should find, so accuracy can be
measured field by field, not eyeballed.

The goal is a shared, open benchmark: one place where every Canadian receipt layout an
extractor can meet is described, generated and scored.

## What is inside

```
corpus/<family>/NNNN.png    clean print, as it leaves the thermal printer
corpus/<family>/NNNN.jpg    the same, degraded like a phone photo (fading, shading, fold,
                            blur, rotation, perspective, noise, JPEG)
corpus/<family>/NNNN.json   ground truth + exact printed text lines + degradation parameters
docs/templates/             one template sheet per family: structure, vocabulary, source
docs/sources/               official documents some templates are drawn from
src/                        the generator (Python, Pillow, numpy)
```

### Families

| Family | Template source | Status |
|---|---|---|
| `restaurant_websrm` | Revenu Québec, official restaurant-sector invoice sample (mandatory billing, MEV-WEB), July 2025 | done |
| `taxi_websrm` | Revenu Québec, official sample for paid passenger transportation, July 2025 | done |
| `grocery_chain` | real receipts from a large Québec grocery chain (structure only); card slip printed inside the receipt | done |
| `crown_store_tax_included` | real receipts from two Québec crown corporations (alcohol, cannabis): prices include taxes, inline card slip | done |
| `payment_terminal_slip` | real tickets from a crown corporation and a Québec convenience store: the card slip printed on its own, with no items or purchase total; standalone terminal variant (*MM/DD/YY* date, `$12.50`) | done |
| `big_box_retail` | a real receipt from a large Québec office-supply and electronics chain: item prices with a decimal point and a glued tax code (`49.99B`), totals with a decimal comma, eco fee included | done |
| `professional_invoice` | a real invoice from a Québec veterinary clinic: client, patient, `7-nov.-2026` date with no time, GST/QST numbers without suffix | done |
| pharmacy, hardware store | observation | wanted |
| gas station, parking | observation | wanted |
| outside Québec (HST; GST + PST) | observation | wanted |

## Fake data, guaranteed fake

A generator of realistic receipts is also, in other hands, a generator of fake receipts.
The guardrails live in the code, not in good intentions:

- **Fictitious merchants**, assembled from pieces; never an existing brand.
- **Phone numbers in the 555-01XX block**, reserved for fiction by the North American
  Numbering Plan.
- **GST and QST numbers that deliberately fail the Luhn check**: the shape is right
  (9 digits + RT0001, 10 digits + TQ0001), the number can belong to no one.
- **A "SPÉCIMEN" line printed on every receipt**, a QR code pointing to this repository,
  URLs on `.example`, and placeholder surnames (`Doh`, `Untel`…) for any person named.

## Usage

```sh
uv sync
uv run synthetic-receipts-canada generate --family restaurant_websrm --count 100 --seed 1 --out corpus
uv run synthetic-receipts-canada generate --family all --count 20 --severity heavy --paper 58 --out out
```

Each receipt is drawn from its own pseudo-random generator, seeded by
`(seed, family, index)`: regenerating one receipt or adding more never changes the ones
already produced.

### Ground truth format (`schema_version` 1)

```json
{
  "family": "restaurant_websrm",
  "country": "CA", "province": "QC", "currency": "CAD", "language": "fr",
  "merchant": {"name": "...", "address_lines": ["...", "..."], "phone": "514 555-0123"},
  "datetime": "2025-03-14T18:42:07",
  "transaction_number": "048213",
  "items": [{"qty": 1, "description": "Spaghetti", "unit_price_cents": 1200,
             "line_total_cents": 1200, "tax_flags": "FP"}],
  "subtotal_cents": 1800,
  "taxes": [{"kind": "GST", "label": "TPS", "rate": "0.05", "cents": 90},
            {"kind": "QST", "label": "TVQ", "rate": "0.09975", "cents": 180}],
  "total_cents": 2070,
  "tip_cents": 300,
  "gst_number": "123456784RT0001",
  "qst_number": "1234567895TQ0001",
  "payment_method": "debit",
  "document_kind": "closing_receipt",
  "websrm": {"transaction_id": "...", "device_id": "...", "qr_url": "...", "processed_at": "..."},
  "text_lines": ["...", "..."],
  "files": {"clean": "0001.png", "degraded": "0001.jpg"},
  "degradation": {"blur_radius": 0.8, "rotation_degrees": -2.1, "...": "..."}
}
```

A field absent from the receipt is `null`, never a default value. Some families add
fields, described in their template sheet:

- `grocery_chain`: the base of each tax (`taxes[].base_cents`), payment tenders
  (`tenders`), cash rounding (`cash_rounding_cents`), change, and the card slip (`card`).
- `crown_store_tax_included`: taxes marked `included`, and a `subtotal_cents` that is not
  printed and must be recomputed.
- `payment_terminal_slip`: only `tenders` and `card`; `total_cents` is `null`
  (`document_kind`: `payment_slip`). Its `standalone_terminal` variant always prints on
  58 mm paper, whatever `--paper` says.
- `big_box_retail`: `upc`, `sku` and `eco_fee_included` per item, `associate_id`, and a
  `cash_rounding_cents` that is not printed.
- `professional_invoice`: the `client` (name, file number, address), the `patient`, the
  printed `balance_cents`, an unprinted `cash_rounding_cents`; `datetime` is a date only.

Amounts are **integer cents**, rounded half up like a cash register. `total_cents` is the
total of the supply (subtotal + taxes); the tip is separate, as on the receipt. Cash
payments round to the nearest 5 cents, as everywhere in Canada since the cent was
withdrawn in 2013; the total keeps its cents. `text_lines` is the exact printed text, line
by line: it lets an extractor be tested without OCR.

## Contributing: help cover every receipt in Canada

This project gets better with every receipt layout it learns. **You do not need to share
a receipt to contribute**, and you must not: a contribution is a description of a
receipt's *structure*, written from a receipt you have in hand, with every value invented.

What helps most:

- **Receipts from the other provinces and territories.** Ontario and the Atlantic
  provinces (HST), British Columbia, Manitoba and Saskatchewan (GST + PST), Alberta and
  the territories (GST only). English receipts, bilingual receipts, other date formats.
- **Store types not covered yet**: pharmacy, hardware store, gas station, parking,
  restaurant chains, online-order receipts, returns and refunds, credit-card slips.
- **Traps you have seen break an extractor**: a total printed twice, a tax line that looks
  like a price, a date that reads two ways.

How to contribute a template:

1. Read [`CLAUDE.md`](CLAUDE.md), the contributor guide (also read by coding agents). Its
   first section, *no real data*, is not negotiable.
2. Write the template sheet first, in `docs/templates/`, modeled on
   [`grocery-chain.md`](docs/templates/grocery-chain.md): the source in general terms ("a
   large Ontario pharmacy chain"), a table of blocks with invented examples, the traps for
   an extractor, the variation to generate, and what was not observed.
3. Open an issue with the [*Propose a receipt template*](https://github.com/Ragnarush/synthetic-receipts-canada/issues/new?template=propose-template.yml)
   form, or a pull request with the sheet. Code can follow from you or from someone else;
   the sheet alone is already a contribution.

A trap you have seen fool an extractor goes in a [*Report an extractor
trap*](https://github.com/Ragnarush/synthetic-receipts-canada/issues/new?template=extractor-trap.yml)
issue, shown with a generated receipt or with lines you write yourself.

Never commit a real receipt, a photo, a crop, or any value copied from one: no store
name, address, phone, tax number, card digits, cashier, reference or authorization
number, date or amount.

### Beyond Canada

The ground truth already carries `country`, `province`, `currency` and `language`, so
other countries fit the same format: US sales taxes, Mexican CFDI invoices, Brazilian NFC-e
receipts, European VAT receipts. Each country needs its own fake-data guardrails (a phone
range reserved for fiction, tax numbers that fail their checksum) and its own tax rules
before its first family. If you want to start one, open an issue first so the shared
pieces are designed once.

## Credit and citation

Created by **Ragnarush** in 2026. If you use the corpus or the generator, please credit
the project: GitHub's "Cite this repository" button gives a ready citation (from
[`CITATION.cff`](CITATION.cff)). Forks and redistributions keep the [`NOTICE`](NOTICE)
file, as the Apache License 2.0 requires, and credit the corpus as CC BY 4.0 requires,
for example: *"Synthetic receipts from synthetic-receipts-canada by Ragnarush, CC BY
4.0."*

## Licenses

- Code (`src/`): Apache License 2.0, see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
- Corpus and template sheets (`corpus/`, `docs/templates/`): Creative Commons Attribution
  4.0, see [`LICENSE-DATA`](LICENSE-DATA).
- `docs/sources/`: documents from Revenu Québec, reproduced for reference; they remain
  the property of their author.
