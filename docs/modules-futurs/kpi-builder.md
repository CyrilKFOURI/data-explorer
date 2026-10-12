# Module Builder KPI — `/d/:id/kpi`

> **Statut : futur (Sprint 6). Ne pas implémenter avant la V1.**

Construire un indicateur agrégé dans le temps :

- Grain temporel (jour, semaine, mois, trimestre, année) et colonne de date de référence
- Regroupement sur une ou plusieurs colonnes
- Mesure : comptage de lignes, ou somme / moyenne / médiane / min / max / nombre de distincts d'une colonne numérique
- Période dédiée, indépendante des filtres globaux (ou combinée, au choix)
- Styles : barres, ligne, aire, aire empilée, barres + ligne de part en % (double axe)
- Tableau croisé (pivot) lignes × colonnes à partir du même calcul
- Calcul déclenché par un bouton (pas à chaque changement de réglage)
- KPI enregistrables (`kpi_definitions`) et réaffichables
