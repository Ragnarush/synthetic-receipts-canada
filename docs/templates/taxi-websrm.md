# Template `taxi_websrm` — paid passenger transportation (Québec)

**Source.** Revenu Québec, *Exemple de facture – Secteur du transport rémunéré de personnes*
(sample bill, paid passenger transportation sector), image of July 2025:
`docs/sources/revenu-quebec-exemple-facture-taxi-2025-07.png`. Mandatory with a
second-generation sales recording system (SEV) since January 1, 2026.

Same 20 elements in the same order as `restaurant-websrm.md`. Observed differences:

- the **total amount is printed double height under the name**, before the date;
- a single item, `1 Tarif taxi.   15,80 $ FP`;
- an information line `redevance@0,90 $` under the item: the fee (*redevance*) is
  **already included** in the fare and is not added to it (subtotal = fare);
- no establishment address (vehicle).

**Trap for an extractor.** The large amount at the top is the total, not the subtotal;
`redevance@0,90 $` is an amount not to be counted.
