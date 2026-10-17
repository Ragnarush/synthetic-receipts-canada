# synthetic-receipts-canada

Reçus canadiens synthétiques, Québec d'abord, avec la vérité attendue pour chaque image.
Pour tester un moteur OCR ou un extracteur de champs (commerçant, date, sous-total,
TPS, TVQ, total) sans manipuler un seul reçu réel.

*Synthetic Canadian receipts, Québec first, each with its ground truth, for testing OCR
engines and receipt-field extractors. English summary at the end.*

## Pourquoi

Il n'existe aucun jeu public de reçus québécois ou canadiens. Les jeux connus (SROIE,
CORD) sont malaisiens ou indonésiens, en anglais, sans TPS/TVQ. Et un reçu réel est une
donnée personnelle : quatre derniers chiffres d'une carte, numéro de membre, nom de
client. Ce dépôt contourne les deux problèmes : les reçus sont **générés**, à partir de
gabarits qui reproduisent la **structure** des reçus réels, et remplis de **fausses
données vérifiablement fausses**.

## Ce qu'il y a dedans

```
corpus/<famille>/NNNN.png    impression propre, telle que sortie de l'imprimante thermique
corpus/<famille>/NNNN.jpg    la même, dégradée comme une photo de téléphone (délavage,
                             ombrage, pli, flou, rotation, perspective, bruit, JPEG)
corpus/<famille>/NNNN.json   vérité attendue + lignes de texte exactes + paramètres de dégradation
docs/templates/              un gabarit par famille : structure, vocabulaire, source
docs/sources/                documents officiels dont les gabarits sont tirés
src/                         le générateur (Python, Pillow, numpy)
```

### Familles

| Famille | Source du gabarit | État |
|---|---|---|
| `restaurant_websrm` | Revenu Québec, exemple officiel de facture du secteur de la restauration (facturation obligatoire, MEV-WEB), juillet 2025 | livrée |
| `taxi_websrm` | Revenu Québec, exemple officiel du transport rémunéré de personnes, juillet 2025 | livrée |
| `grocery_chain` | observation de reçus réels d'une grande chaîne d'épicerie québécoise (structure seulement) ; bordereau du terminal intégré | livrée |
| bordereau de terminal de paiement seul | observation | à venir |
| société d'État à taxes incluses (alcool, cannabis) | observation | à venir |
| grande surface (fournitures, électronique) | observation | à venir |
| facture de services professionnels | observation | à venir |
| pharmacie, quincaillerie | observation | à venir |
| essence, stationnement | observation | à venir |
| hors Québec (TVH ; TPS + TVP) | observation | à venir |

## Fausses données, garanties fausses

Un générateur de reçus réalistes est aussi, entre d'autres mains, un générateur de faux
reçus. Quatre garde-fous, dans le code et non dans la bonne volonté :

- **Commerces fictifs**, assemblés à partir de morceaux ; jamais une enseigne existante.
- **Téléphones dans le bloc 555-01XX**, réservé à la fiction par le plan de numérotation
  nord-américain.
- **Numéros de TPS et de TVQ qui échouent volontairement la vérification de Luhn** : la
  forme est juste (9 chiffres + RT0001, 10 chiffres + TQ0001), le numéro ne peut
  appartenir à personne.
- **Une ligne « SPÉCIMEN » imprimée sur chaque reçu** et un code QR qui pointe vers ce
  dépôt, pas vers Revenu Québec.

## Utilisation

```sh
uv sync
uv run synthetic-receipts-canada generate --family restaurant_websrm --count 100 --seed 1 --out corpus
uv run synthetic-receipts-canada generate --family all --count 20 --severity heavy --paper 58 --out out
```

Chaque reçu est tiré d'un générateur pseudo-aléatoire propre, semé par
`(seed, famille, index)` : en regénérer un ou en ajouter d'autres ne change jamais ceux
déjà produits.

### Format de la vérité attendue (`schema_version` 1)

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

Certaines familles ajoutent des champs, décrits dans leur gabarit : `grocery_chain` donne
l'assiette de chaque taxe (`taxes[].base_cents`), les modes de paiement (`tenders`),
l'arrondi au comptant, la monnaie rendue et le bordereau de carte (`card`). Un champ
absent du reçu vaut `null`, jamais une valeur par défaut.

Les montants sont en **cents entiers**, arrondis à la demi-unité supérieure comme une
caisse. `total_cents` est le total de la fourniture (sous-total + taxes) ; le pourboire
est à part, comme sur le reçu. `text_lines` est le texte exact imprimé, ligne par ligne :
il permet de tester un extracteur sans passer par l'OCR.

## Contribuer un gabarit

Un gabarit décrit une **structure**, jamais un reçu précis : ordre des blocs,
vocabulaire, alignement, largeur de papier, marqueurs de taxes. Voir
`docs/templates/restaurant-websrm.md` pour la forme attendue, avec la source de chaque
élément. Un reçu réel ne doit jamais être versé dans ce dépôt, même anonymisé.

## Licences

- Code (`src/`) : Apache License 2.0, voir `LICENSE`.
- Corpus et gabarits (`corpus/`, `docs/templates/`) : Creative Commons Attribution 4.0,
  voir `LICENSE-DATA`.
- `docs/sources/` : documents de Revenu Québec, reproduits à titre de référence ; ils
  restent la propriété de leur auteur.

---

## English summary

No public dataset of Québec or Canadian receipts exists, and real receipts carry personal
data. This repository generates receipts from templates that copy the *structure* of real
ones (the restaurant and taxi families follow Revenu Québec's official mandatory-billing
samples; the grocery family copies the structure of a large Québec chain's receipts, inline
card slip included) and fills them with verifiably fake data: fictitious merchants, 555-01XX
phone numbers, GST/QST numbers that deliberately fail the Luhn check, a printed "SPÉCIMEN" line,
a QR code pointing here. Each receipt comes as a clean print, a degraded phone-photo
version, and a JSON ground truth with integer-cent amounts and the exact printed text
lines. Code is Apache-2.0; data is CC BY 4.0.
