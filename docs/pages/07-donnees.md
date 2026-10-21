# Données — `/d/:id/data`

## Rôle

Voir les **lignes brutes** après filtres : point de contrôle et sortie des données.

## Contenu

- Barre d'outils : mode d'affichage, recherche, « N of M columns » (réafficher les colonnes masquées), compte des lignes de la vue, menu Export
- Table virtualisée (défilement fluide sur des millions de lignes, chargées par blocs de 100), numéro de ligne du fichier en première colonne (figée)
- En-têtes de colonne : nom + `TypeBadge` + mini-histogramme ; clic sur le nom → tri (croissant → décroissant → ordre du fichier) ; menu → trier, filtrer sur cette colonne, masquer, figer à gauche, ouvrir la fiche
- Cellules : nombres alignés à droite au format de la locale, dates lisibles, vides marqués (« — » grisé), texte long tronqué avec info-bulle ; une valeur que le type choisi ne sait pas lire s'affiche brute, en italique, avec un avertissement
- Modes d'affichage : premières lignes · **échantillon aléatoire** (10 000 lignes au plus, reproductible) · lignes dupliquées seulement (les copies se suivent) · lignes avec manquants seulement
- Recherche plein texte (insensible à la casse) dans le sous-ensemble filtré
- Mode, recherche et tri vivent dans l'URL ; colonnes masquées et figées mémorisées par dataset

## Exports

- La vue courante (filtres, mode, recherche, tri) → CSV, Parquet, Excel (colonnes visibles ou toutes), valeurs typées ; Excel limité à 1 048 575 lignes (sinon proposer CSV / Parquet)
- Résumé des statistiques de toutes les colonnes → CSV (sur les lignes filtrées)
- Graphiques : PNG depuis chaque carte (déjà en place)
- Rapport HTML complet du dataset (« Report (HTML) » dans le menu Export, comme le bouton de la Vue d'ensemble, voir la [025](../features/025-rapport-html/spec.md))
