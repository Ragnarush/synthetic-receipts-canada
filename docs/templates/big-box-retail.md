# Gabarit `big_box_retail` — grande surface de fournitures et d'électronique (Québec)

**Source.** Observation d'un reçu réel d'une grande chaîne de fournitures de bureau et
d'électronique, imprimé au Québec en 2026, payé au comptant. **Seule la structure est
reprise** ; enseigne, adresse, numéros et articles sont fictifs, et les exemples ci-dessous
aussi.

**Papier.** Thermique 80 mm (42 colonnes) ; en 58 mm, les lignes longues se replient.

| Bloc | Forme observée | Vérité attendue |
|---|---|---|
| Enseigne | nom de la chaîne, centré, taille normale | `merchant.name` |
| Magasin | nom de la ville seul, centré | — |
| Adresse | `12 Rue-des-Fictifs St` (**forme anglaise**, type de voie à la fin) / `Ville, QC A1B 2C3` / `819-555-0123` | `merchant.address_lines`, `merchant.phone` |
| Transaction | `VENTE` à gauche ; à droite `00012 001 004 12345` (quatre groupes, le dernier est le n° de transaction) | `transaction_number` |
| Date | à droite `0042 15/01/26 10:20` : n° de magasin, puis *JJ/MM/AA* et l'heure | `store_number`, `datetime` |
| Associé | `1234567` seul sur sa ligne, sans étiquette | `associate_id` |
| Article | `1    Clavier sans fil Doh` : quantité, puis description abrégée | `items[].qty`, `items[].description` |
| Code | `     012345678905              49.99B` : code UPC à 12 chiffres, prix en **point décimal** suivi du code de taxe `B` | `items[].upc`, `items[].line_total_cents`, `items[].tax_flags` |
| Écofrais | `     UGS 123456 d'écofrais inclus` sous les articles électroniques : numéro UGS et écofrais **compris dans le prix** | `items[].sku`, `items[].eco_fee_included` |
| Sous-total | `Total partiel   49,99` (**virgule**) | `subtotal_cents` |
| Taxes | `     5.00% TPS   2,50` / `     9.975% TVQ   4,99` (taux en point, montant en virgule) | `taxes[]` |
| Total | `Total   57,48 $` | `total_cents` |
| Paiement | `Comptant   60,00` / `Comptant Rendu   2,52` | `tenders[]`, `change_cents` |
| Avis | deux encadrés d'étoiles : produits non retournables, programme d'échange d'appareils | — |
| Remerciement | `Merci d'avoir magasiné chez <enseigne>` | — |
| Inscriptions | `TPS : 123456789 - TVQ : 1234567890TQ0001AB` sur une ligne | `gst_number`, `qst_number` |
| Sondage | invitation au concours, **code QR**, `textez XYZ42 au 12345`, `ou visitez <site>/survey/42`, mentions légales, adresse des règlements | — |
| Code-barres | code-barres avec ses chiffres espacés : magasin + date *JJMMAA* + transaction + caisse | — |

**Trois écritures des nombres sur un même reçu.** Le prix de l'article est en point
(`49.99B`), les totaux en virgule (`49,99`), les taux en point avec `%` (`9.975%`).

**Taxes.** TPS 5 % et TVQ 9,975 % sur le total partiel, arrondies au cent (demi
supérieur). L'écofrais est déjà dans le prix et donc taxé.

**Comptant.** Seul le comptant a été observé, avec un total déjà multiple de 5 ¢ : aucune
ligne d'arrondi n'est imprimée. Le générateur ne produit que des totaux multiples de
5 ¢ et ne crée pas de ligne d'arrondi.

**Pièges utiles pour un extracteur.**
- `B` collé au prix (`49.99B`) : il faut le retirer, sans perdre le montant.
- Le numéro TPS est imprimé **sans** `RT0001` (9 chiffres seuls), et le numéro TVQ porte
  deux lettres de plus après `TQ0001`.
- `Total partiel` puis `Total` : un extracteur qui cherche « Total » au premier match
  prend le sous-total.
- `Comptant Rendu` est la monnaie, pas un paiement.
- *JJ/MM/AA* (`07/11/26`), précédé du numéro de magasin (`0042`), qui peut être lu comme
  une heure ou un montant.
- Lignes de chiffres sans étiquette : le groupe `00012 001 004 12345`, l'associé
  `1234567`, l'UPC, l'UGS, les chiffres sous le code-barres.
- Le prix du concours (`500 $`) est un montant dans le texte promotionnel.

**Variation générée.** Enseigne, ville, adresse, 1 à 5 articles de fournitures et
d'électronique (écofrais sur l'électronique seulement), montant remis (billet supérieur
ou somme exacte), présence des encadrés d'avis.

**Hors gabarit (pas encore observé).** Paiement par carte (bordereau intégré ou non),
arrondi au comptant, quantité supérieure à 1, rabais et prix réduits, retours, article
non taxable (autre code que `B`), programme de fidélité.
