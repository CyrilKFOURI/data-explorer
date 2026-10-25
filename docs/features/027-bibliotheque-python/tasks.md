# 027 — Tâches

## Phase 1 — moteurs de calcul

- [x] Spec et tâches, branche `feature/python-library`
- [x] 1. Paquet vide `packages/cyfouri-data-explorer` (hatchling, src), source uv éditable dans `backend/pyproject.toml`, job CI « library » (paquet seul : lint, types, tests)
- [x] 2. Domaine pur déplacé dans le paquet (imports réécrits), services SQLite dans `app/services/`, `AppError` = `ExplorerError`, Dockerfile mis à jour ; tous les tests verts
- [x] 3. `catalog.py` (protocoles, ColumnView, logique des colonnes), `Dataset`, `dx.open()` avec cache, `from_pandas` / `from_arrow`, `ds.types`, `ds.retype()`, `ds.exclude()`
- [x] 4. Services d'analyse sur le protocole `Catalog` ; `ds.overview()`, `ds.variable()` (+ fits, outliers, transformations), `ds.compare()`, `ds.correlations()`, `ds.rows()`, `ds.where()`
- [x] 5. `ds.report(path)`
- [x] 6. Séries temporelles (`ds.timeseries()`), KPI (`ds.kpi_suggestions()`, `ds.kpi()`), ML (`ds.ml()`), synthétique (`ds.synthetic()`) ; calcul des runs dans le paquet
- [x] 7. `to_dict()` / `to_pandas()`, test de garde (aucun import d'app), test de parité, README du paquet, notebook d'exemple, ARCHITECTURE / PLAN / README ; tests, lint, types, image Docker

Mesuré :
- **Paquet seul** (DuckDB 2.0, pandas 3.1) : 588 tests unitaires passent, plus ceux de la façade.
- **App** (DuckDB 1.5.6) : 198 tests d'API passent, dont la parité app = bibliothèque.
- **Roue** installée dans un environnement vierge : ouverture, analyses, ML, synthétique et rapport fonctionnent sans l'extra `[ml]`.
- **Image Docker** : +5 Mo.
- **Import** : 5,8 s à froid. Le ML et le synthétique se chargent au premier usage.

Corrigé au passage :
- `connection.sql()` refuse un résultat non terminé sous DuckDB 2 : retour à `execute()` dans `correlations/matrix.py`.
- Optuna était importé dès le chargement du paquet : il ne l'est plus qu'au début d'une optimisation.

## Phase 2 — visuels

- [x] Accord pour plotly (2026-10-25) : extra `[plot]`, hors de l'image Docker
- [x] `plots/theme.py` : tokens clair et sombre (tokens.css), mise en page de base, fusion des axes et des marges
- [x] Figures portées depuis le frontend : carte de colonne (barres, camembert, histogramme, boîte, chronologie), variable (KDE, ECDF, violon, QQ, lois, calendrier, mots), compare (nuage + régression, densité, 3D, boîtes / violons / moyennes, avec couleur, tableau croisé, empilé, séries), corrélations, séries temporelles (vue d'ensemble, saisonnalité, superposition par année, décomposition, série transformée, ACF / PACF, volatilité, résidus, ruptures, prévision), ML (prédit / réel, résidus, confusion, ROC, PR, calibration, coefficients, importances, courbe d'apprentissage, permutation, SHAP, dépendance, cascade d'une ligne, essais d'optimisation, superposition de modèles), synthétique (moyennes, écarts-types, ACP, liens, DCR, scores, colonne, paire, séquences), KPI (tous les types de graphique et modes « Show as »)
- [x] `dx.plot()`, `ds.plot()`, `ds.chart()` ; tests (`test_plots.py`, 28 cas) ; galerie de vérification visuelle en clair et en sombre ; README, notebook
- Écarts voulus avec l'app : fond de la couleur de surface (une cellule de notebook n'a pas de fond de page), zoom permis (axes non figés), marge d'un côté élargi fusionnée avec les autres (dans l'app, les figures à étiquettes longues retombaient sur les marges par défaut de plotly)
- Corrigé en route : `to_dict()` prenait tout objet ayant un attribut `result` pour un modèle ; domaine d'axe de la décomposition à −2,8e-17 (arrondi) refusé par plotly
