# Gabarit `restaurant_websrm` — restaurant, bar, traiteur (Québec)

**Source.** Revenu Québec, *Exemple de facture – Secteur de la restauration* (facturation
obligatoire, système d'enregistrement des ventes certifié / MEV-WEB), image de juillet 2025 :
`docs/sources/revenu-quebec-exemple-facture-restauration-2025-07.png`. La page officielle
numérote 20 éléments ; ils sont repris ci-dessous dans le même ordre. Les éléments entre les
deux suites de « = » sont prescrits et ordonnés ; avant la première et après la deuxième,
le commerçant peut ajouter ce qu'il veut (nom du serveur, remerciement, sondage, logo).

**Papier.** Thermique 80 mm (42 colonnes) le plus souvent ; 58 mm (32 colonnes) existe.
Police à chasse fixe. Le nom du commerce est souvent en double hauteur ou remplacé par un logo.

| # | Élément | Forme observée | Dans la vérité attendue |
|---|---|---|---|
| 1 | Nom sous lequel l'entreprise fait affaire, adresse complète de l'établissement | centré, 2 à 3 lignes | `merchant` |
| 2 | Moment de la transmission | `AAAA-MM-JJ HH:MM:SS` | `datetime` |
| 3 | Numéro de transaction du SEV | `TRANSACTION #123456` | `transaction_number` |
| 4 | Description de chaque bien ou service | `1 Spaghetti` + prix | `items[]` |
| 5 | Taxes applicables par article | `FP` (fédérale, provinciale), `FPS` (+ taxe supplémentaire, alcool) | `items[].tax_flags` |
| 6 | Sous-total avant taxes | `SOUS-TOTAL   18,00 $` | `subtotal_cents` |
| 7 | Numéro d'inscription TPS | `TPS: 123456789   RT 0001` | `gst_number` |
| 8 | Numéro d'inscription TVQ | `TVQ: 1234567890  TQ 0001` | `qst_number` |
| 9 | Mode de paiement (reçu de fermeture seulement) | `CARTE DE DÉBIT`, `CARTE DE CRÉDIT`, `COMPTANT` | `payment_method` |
| 10 | Note de crédit seulement : nom du client, date de remise | *non généré en v1* | — |
| 11 | Suite de signes `=` | pleine largeur | — |
| 12 | Montant de la TPS | `TPS:   0,90 $` | `taxes[kind=GST]` |
| 13 | Montant de la TVQ | `TVQ:   1,80 $` | `taxes[kind=QST]` |
| 14 | Total de la fourniture (sous-total + TPS + TVQ) | `TOTAL:  20,70 $` ; pourboire à part, après | `total_cents`, `tip_cents` |
| 15 | Mention selon la situation | `PAIEMENT REÇU` ou `FACTURE ORIGINALE` | `document_kind` |
| 16 | Code QR avec adresse Web | ~ moitié de la largeur | `websrm.qr_url` (pointe vers ce dépôt) |
| 17 | Moment du traitement par Revenu Québec | `AAAA-MM-JJ HH:MM:SS`, quelques secondes après #2 | `websrm.processed_at` |
| 18 | Numéro de transaction attribué par Revenu Québec | `ABCD-1234-EFGH-5678` | `websrm.transaction_id` |
| 19 | Identifiant unique de l'appareil | `0001-2345-6789` | `websrm.device_id` |
| 20 | Suite de signes `=` | pleine largeur | — |

**Pièges utiles pour un extracteur.** Deux blocs « TPS/TVQ » sur le même reçu : les
numéros d'inscription (7, 8) et les montants (12, 13). Le mot `TOTAL` apparaît dans
`SOUS-TOTAL` avant d'apparaître seul. Le pourboire suit le total sans en faire partie. La
ligne `Boiss.alc.(t.incl.)` contient un montant-leurre potentiel (« t.incl. »). Le pied
« SPÉCIMEN » doit être ignoré.

**Variation générée.** Commerce, articles (1 à 7, quantités), alcool ou non, reçu de
fermeture (80 %) ou facture originale, mode de paiement, pourboire, ligne du serveur,
remerciement, téléphone, colonnes de montants étroites ou pleine largeur.
