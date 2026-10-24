# 027 — Tâches

## Phase 1 — moteurs de calcul

- [x] Spec et tâches, branche `feature/python-library`
- [ ] 1. Paquet vide `packages/cyfouri-data-explorer` (hatchling, src), source uv éditable dans `backend/pyproject.toml`, job CI « library » (paquet seul : lint, types, tests)
- [ ] 2. Domaine pur déplacé dans le paquet (imports réécrits), services SQLite dans `app/services/`, `AppError` = `ExplorerError`, Dockerfile mis à jour ; tous les tests verts
- [ ] 3. `catalog.py` (protocoles, ColumnView, logique des colonnes), `Dataset`, `dx.open()` avec cache, `from_pandas` / `from_arrow`, `ds.types`, `ds.retype()`, `ds.exclude()`
- [ ] 4. Services d'analyse sur le protocole `Catalog` ; `ds.overview()`, `ds.variable()` (+ fits, outliers, transformations), `ds.compare()`, `ds.correlations()`, `ds.rows()`, `ds.where()`
- [ ] 5. `ds.report(path)`
- [ ] 6. Séries temporelles (`ds.timeseries()`), KPI (`ds.kpi_suggestions()`, `ds.kpi()`), ML (`ds.ml()`), synthétique (`ds.synthetic()`) ; calcul des runs dans le paquet
- [ ] 7. `to_dict()` / `to_pandas()`, test de garde (aucun import d'app), test de parité, README du paquet, notebook d'exemple, ARCHITECTURE / PLAN / README ; tests, lint, types, image Docker

## Phase 2 — visuels

- [ ] Demander l'accord pour plotly, puis `.plot()` avec les mêmes figures que l'app
