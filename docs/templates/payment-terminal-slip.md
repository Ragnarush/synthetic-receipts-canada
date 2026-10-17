# Gabarit `payment_terminal_slip` — bordereau de terminal sur ticket séparé (Québec)

**Source.** Observation de trois tickets réels imprimés en 2026 : deux d'une société
d'État québécoise de vente d'alcool (dont une réimpression) et un d'un dépanneur. Le
terminal de paiement y sort sur un **ticket distinct**, alors que d'autres détaillants
l'intègrent au reçu de vente (voir `grocery-chain.md`, `crown-store-tax-included.md`).
**Seule la structure est reprise** ; enseignes, adresses et numéros sont fictifs, et les
exemples ci-dessous aussi.

Le ticket ne porte **ni articles, ni taxes, ni total d'achat** : seulement l'en-tête du
commerce et le bordereau. C'est un document à part entière qu'un extracteur reçoit
souvent seul (photo du « mauvais » ticket, ou seul papier remis par un petit commerce).

Deux variantes, imprimées par deux terminaux différents :

- `store_header` : la caisse du magasin imprime son en-tête, puis le bordereau
  `RELEVE DE TRANSACTION` (société d'État) ;
- `standalone_terminal` : un terminal autonome, sans caisse reliée, imprime tout lui-même
  (dépanneur).

## Variante `store_header`

**Papier.** Thermique 80 mm (42 colonnes) ; en 58 mm, les lignes longues se replient.

| Bloc | Forme observée | Vérité attendue |
|---|---|---|
| Logo | bannière | `merchant.name` (nom fictif, double hauteur) |
| Adresse | `123, rue X - Ville` / `Ville, QC A1B 2C3` / `819-555-0123` | `merchant` |
| Transaction | `Billet : 12345    Caisse : 1` | `transaction_number` |
| Succursale | `Succursale : 12345  Caissier : 1234567` | `store_number` |
| Date | `Date : 2026/01/15   Heure : 10:20` (*AAAA/MM/JJ*) | `datetime` |
| Réimpression | 5 lignes d'étoiles avec `RÉIMPRESSION`, **une seule fois**, avant le bordereau | `reprint` |
| Titre | `RELEVE DE TRANSACTION` | — |
| Type | `TYPE: ACHAT` | — |
| Compte | `COMPTE: : CHEQUE` ou `COMPTE: : DEFAUT FLASH` (double deux-points tel quel) | `card.account` |
| Montant | `MONTANT:          37.50 $` entre deux traits, **point décimal** | `tenders[0].cents`, `card` |
| Carte | `Type de carte: Interac`, `NUMERO CARTE:    ************0000` | `card.network`, `card.masked_number` |
| Horodatage | `DATE/HEURE:      26/01/15 10:20:45` (*AA/MM/JJ*, à la seconde) | `card.datetime` |
| Références | `NUMERO REF:      0012345678 C`, `AUTOR #:         1A2B3C` | `card.reference`, `card.authorization` |
| Facture | `NUMERO DE FACT:  12345` = le numéro de `Billet` | `transaction_number` |
| Application | `Interac` / `A0000002771010` / ligne de vérification du terminal | — |
| Résultat | `00/001  APPROUVEE - MERCI`, `-- IMPORTANT --`, `Conserver cette copie…`, `*** COPIE DU CLIENT ***` | — |

Le bordereau est celui de `families/_terminal.py`, repris sans changement : il est
identique sur les deux tickets et sur les reçus qui l'intègrent.

**Montant ≠ total d'achat.** Sur le ticket observé en paiement mixte, `MONTANT` ne vaut
que la part payée par débit ; la part au comptant ne figure que sur le reçu de vente.
Dans la vérité attendue, `total_cents` est donc **`null`** (absent du ticket) et le
montant débité vit dans `tenders` et `card`.

**Deux heures.** `Heure : 10:20` de l'en-tête (à la minute) et `DATE/HEURE:` du bordereau
(à la seconde, quelques dizaines de secondes plus tard, parfois la minute suivante). La
vérité garde l'en-tête dans `datetime` et le bordereau dans `card.datetime`.

## Variante `standalone_terminal`

**Papier.** Ticket étroit de terminal, 58 mm (32 colonnes). Caractères gras, `VENTE DEBIT`
et la ligne du montant en grand ; le pied en petits caractères condensés.

| Bloc | Forme observée | Vérité attendue |
|---|---|---|
| Commerce | nom abrégé en majuscules (`DEP GEN DOH ST-QUIDAM`), centré | `merchant.name` |
| Adresse | `123 CHEMIN DU` / `QUIDAM` (repliée au mot) / `VILLE, QC A1B2C3` (code postal **sans espace**) | `merchant.address_lines` |
| Téléphone | `8195550142` (10 chiffres collés) | `merchant.phone` |
| Titre | `VENTE DEBIT`, gras, grand | — |
| Marchand | `IDM: 1234567` (identifiant du marchand) | `card.merchant_id` |
| Terminal | `IDT: 001` à gauche, `No. REF: 00000042` à droite | `card.terminal_id`, `card.reference` |
| Lot | `No Lot: 123001` à gauche, `NRE: 00000042` à droite (= `No. REF`) | `card.batch` |
| Horodatage | `01/15/26` à gauche, `10:20:45` à droite : **MM/JJ/AA** | `datetime`, `card.datetime` |
| Autorisation | `CODE APPR: 1A2B3C` | `card.authorization` |
| Trace | `No Trace: 00123456` | `card.trace` |
| Compte | `DEBIT/PAR DEFAUT` à gauche, `Sans Contact` à droite | `card.account`, `card.entry` |
| Carte | `************0000` seule sur sa ligne | `card.masked_number` |
| Montant | `MONTANT` à gauche, `$12.50` à droite, gras, grand : **symbole avant**, point décimal | `tenders[0].cents` |
| Résultat | `APPROUVE`, centré | — |
| Application | `Interac` / `AID: A0000002771010` / `TVR: 80 00 00 80 00` (octets espacés) | `card.network` |
| Avis | `VOTRE COMPTE SERA DEBITE DU` / `MONTANT CI-DESSUS` / `VEUILLEZ CONSERVER CETTE COPIE` / `POUR LA VERIFICATION DU RELEVE`, condensé | — |
| Pied | `THANK YOU! / MERCI!`, `COPIE CLIENT` | — |

Une seule heure sur le ticket : `datetime` et `card.datetime` valent la même chose, à la
seconde. Pas de numéro de transaction de caisse : `transaction_number` et `store_number`
sont `null`.

## Pièges utiles pour un extracteur (deux variantes)

- Prendre `MONTANT` pour le total de l'achat : vrai seulement si tout a été payé par carte.
- Aucune taxe, aucun numéro TPS/TVQ : un extracteur qui en exige doit rendre « absent »,
  pas zéro.
- Deux formats de date sur le même ticket (*AAAA/MM/JJ* et *AA/MM/JJ*) ; `26/01/15` se lit
  aussi bien *JJ/MM/AA*.
- Point décimal (`37.50 $`) alors que le reçu de vente du même achat est en virgule.
- `Caissier : 1234567`, `NUMERO REF`, `A0000002771010` et la ligne de vérification
  ressemblent à des montants ou à des dates.
- `Billet` et `NUMERO DE FACT` répètent le même numéro : c'est la clé qui relie le ticket
  au reçu de vente.
- *MM/JJ/AA* (`standalone_terminal`) : `04/11/26` est le 11 avril, pas le 4 novembre. Septième
  format de date du corpus, le seul à mettre le mois en premier.
- `$12.50` : symbole avant le nombre, à l'anglaise, sur un ticket en français.
- `No. REF` et `NRE` répètent le même nombre à zéros de tête ; `IDM`, `No Lot`,
  `No Trace` et le téléphone collé sont autant de suites de chiffres sans étiquette de
  montant.
- `TVR: 80 00 00 80 00` ressemble à une ligne de montants.

**Variation générée.** Variante (moitié-moitié). `store_header` : enseigne, succursale,
compte (`CHEQUE` / `DEFAUT FLASH`), montant (paiement complet ou part débit d'un paiement
mixte), réimpression (20 %), 80 et 58 mm. `standalone_terminal` : commerce, adresse
(repliée ou non), petit montant de dépanneur, numéros de
lot et de référence ; toujours en 32 colonnes, même si l'on demande 80 mm, comme le
terminal réel.

**Hors gabarit (pas encore observé).** Carte de crédit, remboursement, transaction
refusée, copie du marchand, pourboire saisi au terminal, reçu de vente de dépanneur
(seul le bordereau a été observé).
