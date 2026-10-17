# synthetic-receipts-canada

Générateur de reçus canadiens synthétiques (Québec d'abord), avec la vérité attendue de
chaque reçu, pour tester un moteur OCR ou un extracteur de champs sans manipuler un seul
reçu réel. Présentation publique : `README.md`. Ce fichier s'adresse à qui modifie le
dépôt, humain ou agent de code : il dit ce qui ne se négocie pas, puis comment travailler.

## Règle absolue : aucune donnée réelle

Ce dépôt est **public**. Un gabarit décrit une **structure** (ordre des blocs, vocabulaire,
alignements, codes de taxe), jamais un reçu précis.

- Aucun reçu réel versé, même anonymisé, même une photo recadrée. Les photos sources
  restent **hors du dépôt** et ne sont jamais copiées dedans, même temporairement.
- Aucune enseigne, succursale, adresse, ville de client, nom de personne ou d'animal,
  numéro TPS/TVQ, numéro de carte (y compris les 4 derniers chiffres), numéro de caissier,
  de référence ou d'autorisation tiré d'un reçu réel. **Ni dans le code, ni dans les
  fiches `docs/templates/`, ni dans le `README.md`, ni dans les messages de commit.**
- **Un exemple s'invente, il ne se recopie pas** : `12345-6789 RT0001`,
  `************0000`, `819-555-0142`, `07/11/26`, `37.50 $`. Ne jamais reprendre un
  montant, une date ou une heure d'un reçu source « pour illustrer » : c'est la fuite la
  plus fréquente (montant repris dans une fiche puis dans le README, date reprise de notes
  de travail).
- Les fiches ne nomment pas l'enseigne observée : « une grande chaîne d'épicerie
  québécoise », « deux sociétés d'État », « un dépanneur ».
- Un message de commit ne décrit pas non plus la source : pas de « l'échantillon tombait sur
  la même ville que le reçu réel ».
- Un tirage au hasard peut retomber sur une valeur réelle (ville et date d'une facture
  observée, par exemple). On l'écarte par une **règle générale** (borner les dates d'une
  famille), jamais en écrivant la valeur réelle dans le code pour l'exclure : ce serait la
  publier.

**Contrôle avant chaque commit d'une famille tirée d'observation** : relire la fiche ligne
par ligne, puis chercher (`grep`) les valeurs des reçus sources dans le diff, le README et
le corpus généré. **Contrôle avant chaque push** : le même `grep` sur **chaque commit**
(`git log -p origin/main..HEAD`) et sur les messages (`git log --format=%B`), pas seulement
sur l'état final, puisqu'une valeur ajoutée puis retirée reste lisible dans l'historique. Si
une fuite est dans un commit non poussé, on corrige ce commit (`git commit --fixup`, puis
`git rebase --autosquash`), on n'ajoute pas un commit correctif par-dessus. Plusieurs fuites
ont déjà été rattrapées ainsi : 4 derniers chiffres de carte, numéro de caissier, montants
et dates repris comme exemples.

Les garde-fous contre l'usage en faux reçus sont **dans le code** et ne s'assouplissent
pas : commerces fictifs assemblés à partir de morceaux (`fakes.py`), téléphones dans le bloc
555-01XX, numéros TPS/TVQ qui **échouent** la vérification de Luhn, ligne « SPÉCIMEN » sur
chaque reçu, QR vers ce dépôt, URL en `.example`, noms de famille de remplissage (`Doh`,
`Untel`…).

## Fidélité à l'observation

Un générateur ne produit que ce qui a été **observé**. Le reste va dans la section « Hors
gabarit » de la fiche, en attendant un reçu qui le montre.

- Une forme non observée ne s'invente pas pour « varier » : un seul mode de compte vu, un
  seul mode de compte généré.
- Une extrapolation inévitable (les autres mois quand seul `sept.` a été vu) est
  **signalée comme telle** dans la fiche.
- Une règle connue s'applique même quand le reçu observé ne la montre pas, mais on ne
  confond pas un hasard de l'observation avec une règle. Deux reçus payés au comptant
  tombaient sur un total multiple de 5 ¢ : ce n'est pas une contrainte. La règle est
  que seul le paiement au comptant s'arrondit aux 5 ¢ (`money.cash_rounded`), le total
  garde ses cents, et l'écart va dans `cash_rounding_cents`, imprimé ou non.
- Un terminal qui imprime toujours sur son propre papier (58 mm) le fait quel que soit
  `--paper` : la famille écrit la largeur réelle dans `paper_width_mm`, et le CLI rend
  l'image à cette largeur.

## Conventions

- Prose (README, fiches, réponses) en **français** ; code, commentaires et messages de
  commit en **anglais**. Commentaires seulement pour le *pourquoi* non évident.
- Commits directement sur `main`, messages détaillés. **Le push reste sur demande
  explicite** : pousser, c'est publier.
- Stager les fichiers nommés, jamais `git add -A` ni `commit -a`.
- L'argent en **cents entiers**, arrondi au demi supérieur (`money.py`), jamais en `float`.

### Vérité attendue

- `null` veut dire « absent du reçu », jamais une valeur par défaut. Un bordereau de
  terminal n'imprime pas le total de l'achat : son `total_cents` est `null`, pas le montant
  débité.
- Clés communes : `schema_version`, `family`, `country`, `province`, `currency`,
  `language`, `paper_width_mm`, `merchant`, `datetime`, `transaction_number`, `items`,
  `subtotal_cents`, `taxes`, `total_cents`, `tip_cents`, `gst_number`, `qst_number`,
  `payment_method`, `document_kind`, `text_lines`. Le CLI ajoute `files` et `degradation`.
- `document_kind` : `sales_receipt`, `original_invoice`, `closing_receipt`,
  `payment_slip`, `invoice`. En ajouter un seulement pour un document de nature différente.
- `datetime` en ISO, à la précision imprimée : à la minute si le reçu donne `10:20`, date
  seule si aucune heure n'est imprimée.
- Une famille à plusieurs variantes écrit `variant` et tire la variante **en premier**.
- Les champs propres à une famille (`card`, `client`, `patient`, `associate_id`…) sont
  décrits dans sa fiche et dans la section du format du `README.md`.
- `text_lines` est le texte exact imprimé : c'est lui que vérifient les contrôles, et lui
  qu'un extracteur reçoit quand il saute l'OCR.

## Structure

```
src/synthetic_receipts_canada/
  cli.py        generate : un RNG par reçu, semé par (seed, famille, index)
  layout.py     Receipt = lignes de texte en colonnes fixes (42 en 80 mm, 32 en 58 mm),
                QR, code-barres, wrap_overflow()
  render.py     rendu en image thermique (Pillow)
  degrade.py    dégradation « photo de téléphone »
  fakes.py      commerces, adresses, personnes, numéros fictifs
  money.py      cents, arrondi, formats fr/en
  families/     un module par famille : generate(rng, paper_mm) -> (Receipt, vérité),
                liste dans families/__init__.py
    _websrm.py       blocs prescrits de la facturation obligatoire (Revenu Québec)
    _terminal.py     bordereau « RELEVE DE TRANSACTION » partagé
    _crown_store.py  en-tête et produits de la société d'État, partagés par deux familles
docs/templates/ une fiche par famille (source, tableau des blocs, pièges, variation)
docs/sources/   documents officiels dont les gabarits WEB-SRM sont tirés
corpus/         échantillon de 20 reçus par famille (seed 1), commité
```

## Ajouter une famille (ou une variante)

1. **Fiche d'abord** (`docs/templates/<famille>.md`, sur le modèle de `grocery-chain.md`) :
   source, tableau bloc → forme observée → champ de vérité, pièges pour un extracteur,
   variation générée, ce qui est hors gabarit (non observé). La faire valider avant le code.
   Si le reçu montre la même nature de document qu'une famille existante, avec un autre
   appareil ou un autre commerce, c'est une **variante** de cette famille.
2. Module `families/<famille>.py`, enregistré dans `families/__init__.py`. Réutiliser
   `_terminal.py`, `_websrm.py` et `_crown_store.py` plutôt que recopier ; ce qui sert à
   deux familles monte dans `layout.py` ou un module `_partagé`. Un tel déplacement ne doit
   changer **ni l'ordre ni le nombre** des tirages aléatoires.
3. Vérifier, sur au moins 200 reçus en 80 mm **et** 200 en 58 mm :
   - l'arithmétique : somme des articles, taxes au cent, paiements = total + arrondi +
     monnaie ;
   - que les montants, dates et numéros imprimés dans `text_lines` concordent avec la
     vérité ;
   - qu'aucune ligne de `text_lines` ne dépasse la largeur du papier ;
   - les garde-fous : Luhn qui échoue, 555-01XX, ligne SPÉCIMEN, noms de remplissage.

   Il n'y a pas encore de suite de tests : ces contrôles s'écrivent pour la famille et se
   lancent avec `uv run python -I`.
4. Regarder au moins une image propre et une dégradée, en 80 et en 58 mm.
5. **Non-régression** : régénérer `--family all --count 20 --seed 1` dans un dossier
   temporaire et vérifier que les familles existantes sont **identiques octet pour octet**
   à `corpus/` (`diff -rq`). Tout tirage ajouté dans un chemin partagé décale les reçus
   existants. Ajouter une variante décale l'échantillon de sa famille : acceptable tant que
   cet échantillon n'est pas poussé, à signaler dans le commit sinon.
6. Copier l'échantillon de la nouvelle famille dans `corpus/`, ajouter la ligne au tableau
   des familles du `README.md` (et les champs propres dans la section du format).
7. Faire le contrôle de fuite avant le commit (voir plus haut), puis commiter en nommant
   les fichiers.

## Commandes

```sh
uv sync
uv run synthetic-receipts-canada generate --family all --count 20 --seed 1 --out /tmp/x
diff -rq /tmp/x corpus     # non-régression : seules les familles nouvelles diffèrent
uv run synthetic-receipts-canada generate --family grocery_chain --count 200 --paper 58 --no-degrade --out /tmp/y
git log -p origin/main..HEAD | grep -nE '<valeurs des reçus sources>'   # avant un push
```

Python lancé sur des fichiers extérieurs : `uv run python -I`.
