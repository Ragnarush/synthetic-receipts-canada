# Gabarit `professional_invoice` — facture de clinique vétérinaire (Québec)

**Source.** Observation d'une facture réelle d'une clinique vétérinaire québécoise,
imprimée en 2026 sur un ticket thermique, payée au comptant. **Seule la structure est
reprise** ; clinique, client, animal, numéros et produits sont fictifs, et les exemples
ci-dessous aussi. La facture réelle porte le nom et l'adresse du client et le nom de son
animal : rien de tout cela n'est repris, pas même la forme du nom de l'animal.

Une facture de services professionnels se distingue d'un reçu de commerce : elle nomme le
**client** (avec son adresse et son numéro de dossier) et le **patient**, et ne porte
**aucune heure**.

**Papier.** Thermique 80 mm. L'original imprime en petits caractères (environ 56
colonnes) ; le générateur reste à 42 colonnes et replie les longues lignes.

| Bloc | Forme observée | Vérité attendue |
|---|---|---|
| Clinique | `Clinique` / `vétérinaire` / `Doh inc`, grand, centré, sur trois lignes | `merchant.name` |
| Adresse | `123 avenue des Fictifs` / `Ville, QC A1B 2C3` | `merchant.address_lines` |
| Téléphone | `Téléphone:  (819)555-0142` (indicatif entre parenthèses, collé) | `merchant.phone` |
| Inscriptions | `TPS: 123456789  TVQ: 1234567890` : **sans** `RT0001` ni `TQ0001` | `gst_number`, `qst_number` |
| Facture | `Facture: 123456` | `transaction_number` |
| Date | `Date: 7-nov.-2026` : *J-mois abrégé.-AAAA*, **pas d'heure** | `datetime` (date seule) |
| Client | `M. Jean Untel (12345)` (civilité, nom, numéro de dossier) / adresse / `Ville, QC  A1B 2C3` (deux espaces avant le code postal) | `client.name`, `client.id`, `client.address_lines` |
| Patient | `Biscuit - 12345` (nom de l'animal, numéro de patient) | `patient.name`, `patient.id` |
| Article | `   1 Antiparasitaire DOH canin 10.1 kg à      43,01 $` : quantité, description, montant à droite ; la description se replie à la ligne suivante, en retrait | `items[]` |
| Sous-total | `Sous-total:   43,01 $`, bloc aligné à droite | `subtotal_cents` |
| Taxes | `TPS(5%):   2,15 $` / `TVQ(9,975%):   4,29 $` (taux en **virgule**) | `taxes[]` |
| Total | `Total:   49,45 $` | `total_cents` |
| Paiement | `7-nov.-2026  Comptant:   50,00 $` : la date du paiement **répétée** devant le mode | `tenders[]` |
| Monnaie | `Monnaie   0,55 $` (sans deux-points), rendue sur le total arrondi aux 5 ¢ | `change_cents`, `cash_rounding_cents` |
| Solde | `Solde:   0,00 $` | `balance_cents` |
| Avis | `AUCUN RETOUR SUR LES MEDICAMENTS…` en majuscules, frais de prescription inclus dans le prix, intérêts sur solde impayé (`2% par mois`, `24%` par an) | — |

**Taxes.** TPS 5 % et TVQ 9,975 % sur le sous-total, arrondies au cent (demi supérieur).

**Comptant.** Depuis le retrait du cent (2013), seul le **paiement au comptant** s'arrondit aux 5 ¢ les
plus proches (x,x1-x,x2 vers le bas, x,x3-x,x4 vers le haut…) ; le total imprimé garde
ses cents. La facture observée avait un total déjà multiple de 5 ¢ ; quand il ne l'est pas,
la monnaie est rendue sur le total arrondi, **sans ligne d'arrondi imprimée** (forme
non observée, déduite de la règle). L'écart vit dans `cash_rounding_cents`, à recalculer.

**Mois abrégés.** Seul `sept.` a été observé. Les autres mois suivent les abréviations
françaises usuelles (`janv.`, `févr.`, `mars`, `avr.`, `mai`, `juin`, `juil.`, `août`,
`sept.`, `oct.`, `nov.`, `déc.`) : c'est une extrapolation, signalée comme telle.

**Pièges utiles pour un extracteur.**
- `7-nov.-2026` : ni chiffres de mois ni barres ; le mois abrégé finit par un point
  collé au tiret.
- Des nombres dans la description (`10.1 kg à 20kg`, en **point**) alors que les montants
  sont en virgule ; ils ne sont pas des prix.
- Trois numéros entre parenthèses ou après un tiret : dossier client, patient, indicatif
  téléphonique.
- Numéros TPS et TVQ nus, sans suffixe : seule l'étiquette les distingue d'autres numéros.
- `Monnaie` puis `Solde: 0,00 $` : deux montants après le total qui ne sont pas des
  paiements ; `Solde` à zéro ne veut pas dire « gratuit ».
- `Comptant` − `Monnaie` ≠ `Total` quand le total ne finit pas par 0 ou 5 : l'arrondi
  n'est pas imprimé, et le solde reste à zéro.
- `2%` et `24%` dans l'avis sur les intérêts ressemblent à des taux de taxe.
- Le nom du client n'est pas le commerçant : le premier nom propre après l'en-tête est
  celui du client.

**Variation générée.** Clinique, client (noms de remplissage), animal (noms inventés,
espèce chien ou chat), 1 à 4 lignes (examen, vaccin, médicament avec tranche de poids,
nourriture), montant remis, présence des avis. Dates en 2024 et 2025 seulement : aucune
facture générée ne tombe dans l'année où la facture source a été imprimée.

**Hors gabarit (pas encore observé).** Carte, paiement partiel avec solde dû, plusieurs
animaux sur une facture, article non taxable, rabais, autres professions (dentiste,
physiothérapeute…), facture sur papier lettre.
