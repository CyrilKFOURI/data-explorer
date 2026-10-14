# 006 — Comparer : tâches

## Backend
- [x] `domain/compare/` : rôle des colonnes (num / cat / date), lignes utilisées, échantillon
- [x] num × num : points, régression (toutes les lignes), densité 2D, Pearson / Spearman / Kendall
- [x] num × cat : stats par groupe (boîte, moyenne, IC), échantillon pour violons ; Welch t / Mann–Whitney / ANOVA / Welch-ANOVA / Kruskal–Wallis / Levene ; tailles d'effet
- [x] cat × cat : contingence, χ², Fisher, V de Cramér
- [x] date × num, date × cat : séries par période
- [x] 3D : points X, Y, Z (+ couleur)
- [x] API `GET /datasets/{id}/compare?x&y&z&color&filters`
- [x] Tests : chaque combinaison vs scipy (Pearson, régression, Welch t, ANOVA, Kruskal, χ²), erreurs, filtres, perf 5 M (`pytest -m slow`)

## Frontend
- [x] Route `/d/$datasetId/compare` (x, y, z, color dans l'URL), entrée Compare active
- [x] Sélecteurs + inverser X/Y ; « Compare with… » depuis la fiche variable
- [x] Vues par combinaison (nuage + régression, densité, boîtes, violons, moyennes ± IC, heatmap, barres 100 %, séries, 3D)
- [x] Panneau des tests : verdict, p, effet et ordre de grandeur, conditions
- [x] Tests : sélecteurs, graphique + tests, inversion, Z, verdicts (60 tests frontend)

## Vérification
- [x] Navigateur : age × income (nuage + régression), segment × price_eur (boîtes, ordre ordinal), country × segment (heatmap), date × revenue par magasin (séries), age × income × price_eur par segment (3D)
