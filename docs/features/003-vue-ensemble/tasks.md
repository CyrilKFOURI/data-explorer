# 003 — Vue d'ensemble : tâches

## Backend
- [x] `domain/typing/dates.py` : parties de date (année, trimestre, mois, année-mois, semaine, jour de semaine, jour du mois, heure), granularité (heure présente, plage, pas typique), pas automatique de timeline
- [x] Profil de date dans le résumé de colonne (`summary.date`), affiché sur la page Columns
- [x] `domain/charts/prepare.py` : histogramme (Freedman–Diaconis 10–60), boîte à moustaches, barres Top N + Others + manquants, ordinal ordonné, discret, garde forte cardinalité, timeline + vues de parties, longueurs de texte, identifiants
- [x] `domain/profiling/` : résumé (lignes, colonnes, vides, doublons de lignes et de colonnes, taille, types), alertes, stats par colonne pour le tri ; cache en mémoire par version des types
- [x] API : `GET /datasets/{id}/overview`, `GET /datasets/{id}/columns/chart`
- [x] Tests : graphiques (12), Vue d'ensemble et API (7) ; bug corrigé : doublons de colonnes avec XOR de hash

## Frontend
- [x] `plotly.js-dist-min`, chargé à la demande ; `charts/Plot.tsx` (thème depuis les tokens, suit clair/sombre, export PNG)
- [x] Palette catégorielle `--chart-1…8` validée (skill dataviz) ; couleurs de type pour les séries uniques
- [x] Figures : barres (horizontales si besoin, Others/manquants atténués), camembert ≤ 5 avec libellés, histogramme, boîte, timeline (axe de dates)
- [x] Bandeau de résumé, alertes repliables (clic → colonne), grille 3/2/1 par ligne, pagination, recherche, filtre par type, tri, Top N, réglages mémorisés
- [x] Carte de variable : chargement à l'affichage, vues, chiffres clés, changement de type, plein écran (toutes les modalités + tableau avec % cumulé), export PNG
- [x] `/d/:id` = Vue d'ensemble ; « Overview » actif dans la barre latérale ; ancienne page provisoire supprimée
- [x] Tests : Vue d'ensemble (6), règles d'affichage (5)

## Vérification
- [x] Navigateur : `typing_traps` (résumé, alertes, 21 cartes, dates Timeline/Month/Day of week/Hour, catégories Top 10 + Others, plein écran)
