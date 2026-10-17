# Gabarit `taxi_websrm` — transport rémunéré de personnes (Québec)

**Source.** Revenu Québec, *Exemple de facture – Secteur du transport rémunéré de personnes*,
image de juillet 2025 : `docs/sources/revenu-quebec-exemple-facture-taxi-2025-07.png`.
Obligatoire avec un SEV de deuxième génération depuis le 1er janvier 2026.

Mêmes 20 éléments et même ordre que `restaurant-websrm.md`. Différences observées :

- le **montant total est imprimé en double hauteur sous le nom**, avant la date ;
- un seul article, `1 Tarif taxi.   15,80 $ FP` ;
- une ligne d'information `redevance@0,90 $` sous l'article : la redevance est **déjà
  comprise** dans le tarif, elle ne s'additionne pas (sous-total = tarif) ;
- pas d'adresse d'établissement (véhicule).

**Piège utile pour un extracteur.** Le montant en gros caractères en haut est le total,
pas le sous-total ; `redevance@0,90 $` est un montant à ne pas compter.
