# Gabarit `crown_store_tax_included` — société d'État, taxes incluses (Québec)

**Source.** Observation de reçus réels de deux sociétés d'État québécoises de vente au
détail (alcool, cannabis), imprimés en 2026, au comptant, par débit et en paiement mixte,
dont des réimpressions. **Seule la structure est reprise** ; enseigne, adresses et
numéros sont fictifs, et les exemples ci-dessous aussi.

Deux variantes, `alcohol` et `cannabis`, partagent l'essentiel : **les prix affichés
comprennent les taxes**. Il n'y a pas de sous-total imprimé, et les lignes TPS et TVQ
portent `(incl.)` : elles sont **déjà dans le total**.

**Papier.** Thermique 80 mm (42 colonnes) ; en 58 mm, les lignes longues se replient.

| Bloc | Variante `alcohol` | Variante `cannabis` | Vérité attendue |
|---|---|---|---|
| Logo | bannière | bannière | `merchant.name` (nom fictif, double hauteur) |
| Adresse | `123, rue X - Ville` / `Ville, QC A1B 2C3` / `819-555-0123` | `123, rue X` / `Ville, QC A1B 2C3` / `Canada` / `8445550123` (10 chiffres collés) | `merchant` |
| Transaction | `Billet : 12345    Caisse : 1` | `Transaction : 12345  Caisse 2` | `transaction_number` |
| Succursale | `Succursale : 12345  Caissier : 1234567` | `Magasin : 12345  Caissier : 123456` | `store_number` |
| Date | `Date : 2026/01/15   Heure : 10:20` (*AAAA/MM/JJ*) | `Date : 15/01/2026   Heure : 10:20` (*JJ/MM/AAAA*) | `datetime` |
| Réimpression | 5 lignes d'étoiles avec `RÉIMPRESSION`, avant les articles et après le pied | — | `reprint` |
| Articles | `Article  Qté  Prix  Montant`, puis le nom sur une ligne et `code  1  37,50 $  37,50 $` sur la suivante | idem, `42,90$` sans espace ; un produit acheté deux fois s'imprime deux fois | `items[]` |
| Total | `Total   37,50 $`, aligné sur la colonne Prix | idem | `total_cents` |
| Taxes | `123456789 RT0001 TPS (incl.)   1,63 $` | numéros imprimés sur **8 chiffres** | `taxes[]` (`included: true`) |
| Paiement | `Comptant 20,00 $` / `ACHAT DÉBIT 17,50 $` / `Remise Comptant 0,00 $` | `Comptant 90,00$` puis `Monnaie` / `Comptant (4,20)$` ; ou `Debit Card` + bordereau complet intégré | `tenders[]`, `change_cents`, `card` |
| Mention | `Taxe spécifique sur les boissons alcooliques incluse` | renvoi vers l'information sur la consommation | — |
| Compteurs | `Nombre d'articles vendus = 1` | idem + `Poids total Articles vendus =  7g` | `declared_weight_g` |
| Pied | code-barres + code alphanumérique `T…` (22 caractères), `Copie client` | idem, `Exemplaire client` | — |

**Calcul des taxes incluses.** Pour un prix P taxes comprises : TPS = P × 5 / 114,975 et
TVQ = P × 9,975 / 114,975, arrondies au cent (demi supérieur). Les deux variantes le
confirment au cent près. `subtotal_cents` de la vérité attendue vaut
total − TPS − TVQ : **il n'est pas imprimé**, c'est ce qu'un extracteur doit recalculer.

**Bordereau intégré (cannabis, débit).** Un résumé (`Debit Card`, carte masquée,
`Numéro d'autorisation`, `Type de transaction : Vente`, `Heure d'autorisation`, ligne de
version du terminal) puis le bordereau `RELEVE DE TRANSACTION` complet. Ce bordereau est
identique d'un détaillant à l'autre (`families/_terminal.py`). Il donne `MONTANT: 42.90 $`
en **point décimal**, alors que le reste du reçu est en virgule, et la date en
*AA/MM/JJ* (`26/01/15 10:20:45`). Côté alcool, le bordereau sort sur un ticket séparé ;
il relève de la famille « bordereau de terminal ».

**Poids déclaré (cannabis).** `Poids total Articles vendus` est l'**équivalent en
cannabis séché** de la réglementation fédérale : 1 g de haschich ou de résine compte pour
4 g. Un sachet de 3,5 g de haschich imprime donc `14g`. Le total reste sous la
limite de possession de 30 g. C'est un nombre-leurre pour un extracteur, pas un montant.

**Pièges utiles pour un extracteur.**
- **Additionner les taxes au total compte deux fois** : `(incl.)` est le seul indice.
- Pas de `SOUS-TOTAL` : un extracteur qui l'exige ne trouve rien ; un extracteur qui
  prend la première somme venue après les articles prend le total.
- Chaque ligne de taxe **commence par le numéro d'inscription** (8 à 10 chiffres).
- La monnaie rendue est **négative entre parenthèses** sous un second `Comptant`.
- Paiement fractionné : `Comptant` et `ACHAT DÉBIT` sont deux montants partiels.
- Trois formats de date selon la variante et le bordereau.
- `Caissier : 1234567` et la ligne de version du terminal ressemblent à des montants.

**Variation générée.** Variante, enseigne, succursale, 1 à 5 articles (doublons
compris), comptant (avec ou sans monnaie), débit, mixte (alcool seulement), réimpression
(alcool, 20 %).

**Hors gabarit (pas encore observé).** Carte de crédit, retours, consigne sur les
contenants, rabais.
