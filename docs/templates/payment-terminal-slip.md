# Gabarit `payment_terminal_slip` — bordereau de terminal sur ticket séparé (Québec)

**Source.** Observation de deux tickets réels imprimés en 2026 par une société d'État
québécoise de vente d'alcool. Le terminal de paiement y sort sur un **ticket distinct**
du reçu de vente, alors que d'autres détaillants l'intègrent au reçu
(voir `grocery-chain.md`, `crown-store-tax-included.md`). L'un des deux est une
réimpression. **Seule la structure est reprise** ; enseigne, adresses et numéros sont
fictifs, et les exemples ci-dessous aussi.

Le ticket ne porte **ni articles, ni taxes, ni total d'achat** : seulement l'en-tête du
magasin et le bordereau. C'est un document à part entière qu'un extracteur reçoit
souvent seul (photo du « mauvais » ticket).

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

**Pièges utiles pour un extracteur.**
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

**Variation générée.** Enseigne, succursale, compte (`CHEQUE` / `DEFAUT FLASH`), montant
(paiement complet ou part débit d'un paiement mixte), réimpression (20 %), 80 et 58 mm.

**Hors gabarit (pas encore observé).** Carte de crédit, remboursement (`TYPE: REMISE`),
transaction refusée, copie du marchand, ticket séparé chez un autre type de commerce.
