# synthetic-receipts-canada

Générateur de reçus canadiens synthétiques (Québec d'abord), avec la vérité attendue de
chaque reçu, pour tester un moteur OCR ou un extracteur de champs sans manipuler un seul
reçu réel. Présentation publique : `README.md`.

## Règle absolue : aucune donnée réelle

Ce dépôt est **public**. Un gabarit décrit une **structure** (ordre des blocs, vocabulaire,
alignements, codes de taxe), jamais un reçu précis.

- Aucun reçu réel versé, même anonymisé, même une photo recadrée.
- Aucune enseigne, succursale, adresse, ville de client, nom de personne, numéro TPS/TVQ,
  numéro de carte (y compris les 4 derniers chiffres), numéro de caissier, de référence ou
  d'autorisation tiré d'un reçu réel. **Ni dans le code, ni dans les fiches `docs/templates/`,
  ni dans les messages de commit.** Les exemples des fiches sont inventés (`12345-6789
  RT0001`, `************0000`, `819-555-0142`…).
- Les fiches ne nomment pas l'enseigne observée : « une grande chaîne d'épicerie
  québécoise », « deux sociétés d'État ».
- Avant chaque commit d'une famille tirée d'observation, **relire la fiche ligne par ligne**
  et y chercher les valeurs des reçus sources (`grep`). Deux fuites ont déjà été rattrapées
  ainsi (4 derniers chiffres de carte, numéro de caissier).

Les garde-fous contre l'usage en faux reçus sont **dans le code** et ne s'assouplissent
pas : commerces fictifs assemblés à partir de morceaux (`fakes.py`), téléphones dans le bloc
555-01XX, numéros TPS/TVQ qui **échouent** la vérification de Luhn, ligne « SPÉCIMEN » sur
chaque reçu, QR vers ce dépôt, URL en `.example`, noms de famille de remplissage (`Doh`,
`Untel`…).

## Conventions

- Prose (README, fiches, réponses) en **français** ; code, commentaires et messages de
  commit en **anglais**. Commentaires seulement pour le *pourquoi* non évident.
- Commits directement sur `main`, messages détaillés. **Le push reste sur demande
  explicite** : pousser, c'est publier.
- Stager les fichiers nommés, jamais `git add -A` ni `commit -a`.
- L'argent en **cents entiers**, arrondi au demi supérieur (`money.py`), jamais en `float`.
- Dans la vérité attendue, `null` veut dire « absent du reçu », jamais une valeur par défaut.

## Structure

```
src/synthetic_receipts_canada/
  layout.py     Receipt = lignes de texte en colonnes fixes (42 en 80 mm, 32 en 58 mm),
                QR, code-barres, wrap_overflow()
  render.py     rendu en image thermique (Pillow)
  degrade.py    dégradation « photo de téléphone »
  fakes.py      commerces, adresses, personnes, numéros fictifs
  money.py      cents, arrondi, formats fr/en
  families/     un module par famille : generate(rng, paper_mm) -> (Receipt, vérité)
    _websrm.py    blocs prescrits de la facturation obligatoire (Revenu Québec)
    _terminal.py  bordereau « RELEVE DE TRANSACTION » partagé
docs/templates/ une fiche par famille (source, tableau des blocs, pièges, variation)
docs/sources/   documents officiels dont les gabarits WEB-SRM sont tirés
corpus/         échantillon de 20 reçus par famille (seed 1), commité
```

## Ajouter une famille

1. **Fiche d'abord** (`docs/templates/<famille>.md`, sur le modèle de `grocery-chain.md`) :
   source, tableau bloc → forme observée → champ de vérité, pièges pour un extracteur,
   variation générée, ce qui est hors gabarit (non observé). La faire valider avant le code.
2. Module `families/<famille>.py`, enregistré dans `families/__init__.py`. Réutiliser
   `_terminal.py` / `_websrm.py` plutôt que recopier ; ce qui sert à deux familles monte dans
   `layout.py` ou un module `_partagé`.
3. Vérifier, sur au moins 200 reçus en 80 mm **et** 200 en 58 mm : l'arithmétique (somme
   des articles, taxes au cent, paiements = total + arrondi + monnaie) et qu'aucune ligne
   de `text_lines` ne dépasse la largeur du papier.
4. Regarder au moins une image propre et une dégradée.
5. **Non-régression** : régénérer `--family all --count 20 --seed 1` dans un dossier
   temporaire et vérifier que les familles existantes sont **identiques octet pour octet**
   à `corpus/` (`diff -rq`). Le RNG est semé par `(seed, famille, index)` : tout tirage
   ajouté dans un chemin partagé décale les reçus existants.
6. Copier l'échantillon de la nouvelle famille dans `corpus/`, ajouter la ligne au tableau
   des familles du `README.md` (et les champs propres dans la section du format).

## Commandes

```sh
uv sync
uv run synthetic-receipts-canada generate --family all --count 20 --seed 1 --out /tmp/x
uv run synthetic-receipts-canada generate --family grocery_chain --count 200 --paper 58 --no-degrade --out /tmp/y
```

Python lancé sur des fichiers extérieurs : `uv run python -I`.
