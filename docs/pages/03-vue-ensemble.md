# Vue d'ensemble — `/d/:id/overview`

## Rôle

Balayer **toutes les variables d'un coup d'œil** et repérer ce qui mérite d'être creusé.

## Contenu

0. **En-tête** : nom de la page, chemin de la source, bouton **Export report** à droite (rapport HTML du dataset, sur les lignes filtrées, voir la [025](../features/025-rapport-html/spec.md) : progression dans le bouton, « Cancel » à côté, téléchargement automatique à la fin) ; pour un dataset créé depuis des données synthétiques, la mention « Synthetic, from <source> » avec le lien vers le run (023).
1. **Bandeau de résumé** (transverse, voir [00-transverse.md](00-transverse.md))
2. **Alertes qualité** (repliables) : colonnes vides ou constantes, doublons, types à faible confiance, colonnes très asymétriques, cardinalité extrême. Chaque alerte mène à la colonne concernée.
3. **Barre d'outils de la grille** :
   - Recherche par nom de colonne
   - Filtre par type (puces : numérique, catégoriel, date…) et par alerte
   - Tri : ordre du fichier, nom, % de manquants, cardinalité, asymétrie
   - Top N par défaut des catégoriels (5–50)
   - Variables par page : 6 / 12 / 24 / 48
4. **Grille de variables** : **3 cartes par ligne** (2 puis 1 si la fenêtre rétrécit), **12 par page** par défaut, défilement vertical, pagination en haut et en bas.

## Une carte de variable

- En-tête : nom, `TypeBadge`, étoile (épingler en tête de grille)
- Graphique par défaut selon le type (voir [VISUALS.md](../VISUALS.md)) : histogramme pour un continu, barres Top N pour un catégoriel ou un discret, volume par période pour une date, barre 100 % pour un booléen, chiffres clés (distinctes, doublons) pour un identifiant
- Mini-stats sous le graphique : manquants %, distinctes, et moyenne / médiane ou modalité dominante
- Actions : plein écran, changer de visuel, ouvrir la **fiche variable**, exporter
- **Plein écran** : grand graphique (toutes les modalités pour un catégoriel, qui défile dans 420 px pour laisser le tableau visible), puis les détails de la fiche variable en bref : stats complètes et verdict des 5 tests de normalité pour un numérique, entropie / concentration pour une catégorie, plage / pas / trous pour une date ; bouton « Open variable page »

## Règles

- Règles d'affichage catégorielles appliquées partout : Top N, « Autres », « (manquant) », barres horizontales. Voir [VISUALS.md](../VISUALS.md).
- Les cartes hors écran ne sont rendues qu'en devenant visibles.
- Page, tri, filtres de grille et Top N mémorisés par dataset (stockage local du navigateur).
- Dates : la carte bascule entre Timeline, Month, Day of week et Hour (voir [DATES.md](../DATES.md)).

## Cas limites

0 ligne après filtres : grille remplacée par un état vide avec « Effacer les filtres ». Dataset de plus de 500 colonnes : pagination obligatoire, recherche mise en avant.
