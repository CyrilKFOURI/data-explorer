# Données — `/d/:id/data`

## Rôle

Voir les **lignes brutes** après filtres : point de contrôle et sortie des données.

## Contenu

- Table virtualisée (défilement fluide sur des millions de lignes, chargées par blocs)
- En-têtes de colonne : nom + `TypeBadge` + mini-histogramme ; clic → tri ; menu → filtrer, masquer, figer, ouvrir la fiche
- Cellules : nombres alignés à droite au format de la locale, dates lisibles, vides marqués (« — » grisé), texte long tronqué avec info-bulle
- Modes d'affichage : premières lignes · **échantillon aléatoire** · lignes dupliquées seulement · lignes avec manquants seulement
- Recherche plein texte dans le sous-ensemble filtré

## Exports

- Sous-ensemble filtré → CSV, Parquet, Excel (colonnes visibles ou toutes)
- Résumé des statistiques de toutes les colonnes → CSV
- (Plus tard) rapport HTML complet du dataset
