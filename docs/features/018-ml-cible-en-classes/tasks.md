# 018 — Tâches

Spec : [spec.md](spec.md).

## Choix de réalisation

- **Calcul des limites dans le navigateur** (aperçu < 100 ms) à partir de ce que l'API fournit pour la cible : 1 001 quantiles exacts sur toutes les lignes filtrées (`quantile_disc`, valeurs réellement présentes : les ex-aequo se voient), un histogramme fin (80 classes), un échantillon trié de 5 000 valeurs, min / max / P1 / P99, nombre de lignes et de valeurs distinctes. Les effectifs affichés pendant le réglage sont estimés sur la grille des quantiles (précision 0,1 % des lignes) ; les effectifs exacts sont ceux du run.
- **Natural breaks** : Fisher–Jenks exact (programmation dynamique) sur 1 000 valeurs au plus, prises à intervalles réguliers dans l'échantillon trié (mêmes quantiles) : O(k·n²) reste sous 100 ms pour 10 classes.
- **Le serveur applique les limites reçues** (`classes` en paramètre JSON de `POST /runs` et `POST /preparation` : source, méthode, limites, noms) sur toutes les lignes, intervalles (a, b] ; les classes vides sont retirées ; le run enregistre limites, noms et effectifs exacts.
- **Fuite** : la colonne source est la cible (R-SEL-01) ; R-SEL-06 se calcule contre le **nombre d'origine** (|r|), pas contre les classes.
- **Métriques ordinales** pour toute cible ordonnée (classes de 018 ou catégorie ordinale avec ordre validé) : « exact or off by one » et écart moyen en nombre de classes.
- **Runs** : colonne `classes` ajoutée à `ml_runs` (migration 0006) pour distinguer « price » et « price en 3 classes » dans la liste.
- Glissement des limites en Custom : poignées SVG (`role="slider"`), souris et clavier (flèches, Maj = ×10), plus saisie de la valeur.

## Tâches

- [x] T1 — API `GET /modules/ml/datasets/{id}/targets/{column}/distribution` (filtres actifs).
- [x] T2 — Entraînement et aperçu avec `classes` : découpage, tâche binaire / multiclasse, cible ordonnée, fuite contre le nombre d'origine, run + migration.
- [x] T3 — Métriques ordinales (exact or off by one, écart moyen).
- [x] T4 — Tests backend (découpage côté serveur, fuite, métriques, API, migration).
- [x] T5 — `bins.ts` : equal counts (ex-aequo, fusion), equal width (ignore outliers), natural breaks, arrondi, noms par défaut, effectifs estimés, classes trop petites ; tests des critères d'acceptation.
- [x] T6 — UI : « Predict as [Number | Classes] », panneau (−/+, Split by, Round values, Ignore outliers, histogramme + limites glissables, classes renommables avec intervalle / effectif / % / barre), avertissements avec action, entraînement 600 ms après le dernier changement, suggestion pour les cibles discrètes ≤ 10 valeurs ; résultats : « right or off by one ».
- [x] T7 — Docs (page 11, guide, PLAN, BACKEND_SCHEMA), vérifications, navigateur, commit.

## Écarts et découvertes

- Les limites « Equal counts » exactes pour 2 à 10 classes sont calculées par l'API (`equal_counts`) : la grille de 1 001 quantiles seule donnait jusqu'à ± 0,1 % des lignes, hors du critère « 1 000 ± 1 ».
- Contrôle navigateur : une classe d'une seule ligne (limites Custom collées) faisait planter l'entraînement (la ligne partait dans le test, le target encoding multiclasse ne voyait que 2 classes). Désormais refusé avant le découpage : « Class “Medium” has only 1 row (at least 5 needed) ».
- `TargetEncoder(random_state=…)` est déprécié en scikit-learn 1.9 : remplacé par un `KFold` / `StratifiedKFold` mélangé à graine fixe.
- Le ★ de la liste des runs ne compare plus que des runs notés avec la même métrique (R² et accuracy ne se comparent pas).
