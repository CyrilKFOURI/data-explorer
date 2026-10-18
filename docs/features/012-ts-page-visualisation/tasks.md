# 012 — Séries temporelles : page, vue d'ensemble, saisonnalité, décomposition : tâches

## Socle
- [x] Dépendance `statsmodels` (accord donné) ; limite de taille de l'image CI relevée à 900 Mo
- [x] Registre des modules : `setup(app)` côté backend ; modules « dataset » côté frontend (`/d/$datasetId/...`, types de colonnes requis, grisé sinon) ; module « Hello » retiré

## Backend
- [x] `domain/timeseries/builder.py` : construction de la série partagée avec Comparer (011 refactorisé dessus)
- [x] `series.py` : trous (laisser, interpoler, 0, report), série complète pour les méthodes, longueur de saison
- [x] `methods.py` : tendance (Mann-Kendall ★, Sen ★, Hamed–Rao, Mann-Kendall saisonnier, Cox–Stuart, Spearman, régression linéaire) ; saisonnalité (Kruskal–Wallis ★, périodogramme ★, Friedman, QS, g de Fisher, ACF saisonnière)
- [x] `seasonality.py` : profils calendaires (jour de semaine, mois, trimestre, heure) avec écart à la moyenne hors tendance et Kruskal–Wallis ; une ligne par année (années de bord à 1–2 points écartées)
- [x] `decomposition.py` : STL robuste, MSTL, classique additive / multiplicative ; forces de tendance et de saisonnalité
- [x] Module `modules/timeseries` : `GET …/overview`, `…/seasonality`, `…/decomposition` (configuration par défaut, filtres, méthodes au choix, cache)
- [x] Tests : 37 tests de domaine (méthodes vs références, données synthétiques), 6 tests d'API, perf 5 M lignes (`-m slow`)

## Frontend
- [x] Page `/d/$datasetId/timeseries` : barre de configuration collante (date, valeur, période, agrégation, groupe, série, trous), tout dans l'URL
- [x] Sommaire collant avec un verdict par section ; sections calculées à leur arrivée à l'écran
- [x] Vue d'ensemble : chiffres clés, courbe + moyenne / bande glissantes, curseur de plage, superposition des groupes, méthodes de tendance
- [x] Saisonnalité : boîtes par profil, une ligne par année, méthodes
- [x] Décomposition : méthode, longueur de saison, forces, quatre panneaux alignés
- [x] Rangée « Methods » (+ Add method, choix mémorisé) et tableau des résultats (conclusion, p, statistique, valeur, « What it does »)
- [x] Lien « Analyze as time series → » actif depuis Comparer (prérempli)
- [x] Tests : 4 tests de page + barre latérale

## Docs
- [x] `USER_GUIDE.md` (page Time series), `ARCHITECTURE.md` (modules « dataset », `setup`), `PLAN.md`

## Vérification
- [x] Navigateur : `sales_timeseries` (units, revenue par promo), depuis Comparer, trois sections, clair et sombre
