# Gabarit `grocery_chain` — grande chaîne d'épicerie (Québec)

**Source.** Observation de reçus réels d'une grande chaîne d'épicerie québécoise, imprimés
en 2026 dans deux succursales, au comptant, par débit, par crédit et en paiement mixte, à
la caisse et en libre-service. **Seule la structure est reprise** : ordre des blocs,
vocabulaire, alignements, codes de taxe. Aucun reçu, aucune enseigne, aucun numéro ni nom
réel n'entre dans ce dépôt.

Une épicerie n'est pas soumise à la facturation obligatoire (WEB-SRM) : pas de QR ni de
numéro de transaction de Revenu Québec. Le reçu est imprimé en majuscules **sans accents**
(sauf le bordereau du terminal, voir plus bas).

**Papier.** Thermique 80 mm (42 colonnes). En 58 mm, chaque article passe sur deux lignes.

| Bloc | Forme observée | Dans la vérité attendue |
|---|---|---|
| Logo | bannière de l'enseigne | `merchant.name` (ici le nom fictif, en double hauteur) |
| En-tête, forme A | `ENSEIGNE VILLE (1234)` puis `123,RUE, VILLE` | `merchant.name`, `merchant.address_lines`, `store_number` |
| En-tête, forme B | `ENSEIGNE VILLE` puis `819-555-0142` | `merchant.phone` |
| Rayon | `21-EPICERIE`, `35-CHARCUTERIE`… en gras | `items[].department` |
| Article taxable | `  01234567890    BISCUITS CHOCO` / `        FPMRJ` / montant **au bord droit** | `items[]` |
| Article non taxable | `  01234567891    FROMAGE 600G   MRJ    15.00` : codes et montant **sur la même ligne, montant en colonne du milieu** | `items[]` |
| Quantité | préfixe `(2)` devant le code, puis `2 @ $4.00` et le montant au bord droit | `items[].qty`, `unit_price_cents` |
| Prix promo | `$1.75 lmt 6, $2.50 ch` puis `2 @ $1.75 ch` | `items[].promo` |
| Au poids | code PLU à 4 chiffres, puis `0.740 kg @ $4.39/kg` et le montant | `items[].weight_kg`, `unit_price_cents` (au kg) |
| Consigne | `  CONSIGNE 1` puis montant, ou `2@$0.60` sur la ligne suivante | `items[]` avec `kind: deposit` |
| Article gratuit | `(6)12345  TIMBRE …` / `6 @ $0.00` / `0.00` | `items[]`, montant 0 |
| Sous-total | `SOUS-TOTAL   24.62`, double hauteur | `subtotal_cents` |
| TPS | `F=T.P.S 5%   12.00 @  5.000%` puis le montant au bord droit | `taxes[GST]` : `base_cents`, `cents` |
| TVQ | `P=TVQ 9.975% 12.00 @  9.975%` puis le montant | `taxes[QST]` : `base_cents`, `cents` |
| Total | `TOTAL   26.42`, double hauteur | `total_cents` |
| Nombre d'articles (parfois) | `NOMBRE D'ARTICLES:     12` | — |
| Comptant | `COMPTANT 30.00` / `ARRONDI 0.02 (26.40)` / `MONNAIE 3.60` (double hauteur) | `tenders[]`, `cash_rounding_cents`, `change_cents` |
| Carte | bordereau du terminal **intégré**, puis `DEBIT 12.34` ou `CREDIT 12.34` | `tenders[]`, `card` |
| Fidélité | paragraphe centré : `VOUS AURIEZ PU RECOLTER AU MOINS 1,230 POINTS …` | — |
| Inscriptions | `TPS # 12345-6789 RT0001` ; `TVQ# 1234567890 TQ 0002` **parfois absent** | `gst_number`, `qst_number` (`null` si absent) |
| Direction | `DIRECTEUR DU MAGASIN: PRÉNOM NOM`, parfois le téléphone | — |
| Caisse | `****` puis `2026/01/15   201   201   01 1234   10:20` ; en libre-service `26/01/15 LIBRE-SERV 1 9991 21 1234 10:20` | `datetime` |
| Sondage | paragraphe + `CODE: 011526 102001 1234 01234` | — |

**Codes de taxe par article.** `F` = TPS, `P` = TVQ ; les autres lettres (`M`, `R`, `J`,
`Q`) sont propres à la chaîne et ne touchent pas la taxe. Combinaisons observées : `FPMRJ`
(les deux taxes), `FMRJ` (TPS seulement), `MRJ` et `RQ` (détaxé). Les assiettes TPS et
TVQ peuvent donc **différer**. La consigne n'est pas taxée.

**Arrondi au comptant.** Le total se paie arrondi aux 5 ¢ les plus proches. `ARRONDI`
donne l'écart en valeur absolue, et le montant entre parenthèses est le total arrondi
(montant porté en déduction). Quand le client donne le montant exact, il n'y a pas de
ligne `MONNAIE`.

**Bordereau du terminal intégré.** Entre le total et le paragraphe fidélité :

```
Type de Trans.:  ACHAT
Compte:  DEFAUT              12,34 CAD$
Type de carte:  D BIT
Num,ro de Carte:  ************0000 P
DateTime:        26/01/15 10:20:30
# de Ref.:       0010012345
# d'Autor.:      A1B2C3
Interac
A0000002771010 8000008000
      00/001 APPROUVEE - MERCI
      Conservez cette copie pour v,rification
           de votre rapport financier
          *** COPIE DU CLIENT ***
```

Dans la moitié des reçus observés, le `É` est remplacé par une virgule ou une espace
(`Num,ro`, `v,rification`, `D BIT`). C'est une erreur d'encodage du terminal, et le
générateur la reproduit. Le montant y est en **virgule décimale** (`12,34 CAD$`) alors que
le reste du reçu est en point décimal.

**Pièges utiles pour un extracteur.**
- **Deux colonnes de montants** : la colonne du milieu (article non taxable sur une ligne)
  et le bord droit.
- **Trois montants-leurres sur chaque ligne de taxe** : l'assiette (`75.40`), le taux
  (`5.000%`) et seulement ensuite la taxe.
- **Quatre formats de date sur le même reçu** : `2026/01/15` (pied de caisse),
  `26/01/15` en *AA/MM/JJ* (bordereau, et pied en libre-service) et `011526` en
  *MMJJAA* (code du sondage).
- Le **montant arrondi entre parenthèses** n'est pas le total.
- Le **nombre de points** (`1,230`) a une virgule des milliers.
- Les mots `TOTAL` dans `SOUS-TOTAL`, `DEBIT`/`CREDIT` répétant le montant payé.
- Le nom d'une **personne** (direction du magasin) dans le pied, loin du nom du commerce.

**Variation générée.** Enseigne et succursale, en-tête A ou B, 2 à 22 articles de 3 à 8
rayons, quantités, promos, articles au poids, consignes, timbres gratuits, paiement au
comptant (avec ou sans monnaie), débit, crédit ou mixte, bordereau avec ou sans erreur
d'encodage, TVQ imprimée ou non, caisse ou libre-service, nombre d'articles.

**Hors gabarit (pas encore observé).** Coupons et rabais en ligne négative, retours,
points échangés contre un rabais, sacs.
