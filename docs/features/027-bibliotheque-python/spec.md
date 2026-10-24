# 027 — Bibliothèque Python `cyfouri-data-explorer`

Intention fixée dans [bibliotheque-python.md](../../modules-futurs/bibliotheque-python.md). Design validé avec l'utilisateur le 2026-10-24.

## Objectif

Tout le moteur de l'app utilisable dans un notebook ou un script, sans serveur :

```bash
pip install -e packages/cyfouri-data-explorer   # depuis le dépôt ; pas de PyPI pour l'instant
```
```python
import cyfouri_data_explorer as dx

ds = dx.open("titanic.csv")
ds.types                               # types détectés, rôle, confiance, raisons
ds.retype("Pclass", "categorical_ordinal")
ds.overview()                          # résumé et alertes qualité
ds.variable("Age")                     # stats, normalité, outliers ; .fits() pour les lois
ds.compare("Age", "Survived")          # test choisi selon les types, taille d'effet
ds.correlations()                      # matrice mixte, paires, insights
ds.where("Sex", "in", ["female"]).variable("Age")
ds.timeseries(time="Date", value="Sales").stationarity()
ds.ml(target="Survived").train()
ds.kpi(...)                            # KPI suggérés et calculés
ds.synthetic().generate(rows=1000)
ds.report("titanic.html")
```

**Une seule source de vérité** : l'app et la bibliothèque exécutent le même code. Un correctif statistique profite aux deux. Les chiffres sont identiques au chiffre près.

**Usage visé (1)** : l'utilisateur en notebook. L'API est pensée pour être publiée sur PyPI plus tard (2), et chaque résultat est un objet de données exploitable par un programme (3).

## Phases

1. **Moteurs de calcul**, sans affichage. Chaque résultat est une dataclass avec `.to_dict()`. Les parties tabulaires se convertissent en DataFrame pandas (`.to_pandas()`) ; pandas est déjà installé par statsmodels.
2. **Visuels** : `.plot()` rend les mêmes figures que l'app. Cette phase demande une dépendance (plotly), à faire valider avant de commencer.

## Architecture

```
packages/cyfouri-data-explorer/
  pyproject.toml                 ← nom pip cyfouri-data-explorer, import cyfouri_data_explorer
  src/cyfouri_data_explorer/
    __init__.py                  ← open(), Dataset, exceptions
    dataset.py                   ← Dataset : catalogue en mémoire + façade
    errors.py                    ← ExplorerError et ses sous-classes
    catalog.py                   ← protocoles Catalog / DatasetRef, ColumnView, ColumnRecord, effective()
    typing/ ingestion/ variable/ compare/ correlations/ profiling/ charts/ rows/ filters/
    report/ timeseries/ ml/ kpi/ synthetic/ settings/gpu.py
  tests/
backend/app/                     ← l'app : dépend du paquet (source uv en chemin, éditable)
  services/                      ← ce qui touche à SQLite et à l'espace de travail
```

| Règle | Détail |
|---|---|
| R-LIB-01 | **Le paquet n'importe jamais** FastAPI, uvicorn, `sqlite3` ni `app.*`. Un test le vérifie, et la CI installe le paquet seul, sans l'app. |
| R-LIB-02 | **Les services d'analyse** (variable, compare, corrélations, vue d'ensemble, lignes, rapport, séries temporelles, calcul des KPI) passent dans le paquet. Ils dépendent d'un protocole `Catalog` (`ready(id) -> DatasetRef`, `columns(id) -> list[ColumnView]`). Dans l'app, `ColumnService` (SQLite) le satisfait ; dans la bibliothèque, c'est `Dataset` (en mémoire). |
| R-LIB-03 | **La logique des colonnes** (type effectif, correction de type via `parser_for`, résumé) est dans le paquet. Le stockage SQLite des corrections reste dans l'app. `ds.retype()` et la page Colonnes appliquent donc exactement la même règle. |
| R-LIB-04 | **Restent dans l'app** : SQLite (datasets, colonnes, filtres enregistrés, réglages, KPI enregistrés, runs ML et synthétiques, notes), les tâches de fond, les routes HTTP et l'assistant. |
| R-LIB-05 | **ML et synthétique** : le calcul d'un run (préparation, entraînement, métriques, explications, génération, rapport) est une fonction du paquet. L'app y ajoute la persistance et les jobs ; la bibliothèque l'appelle directement. |
| R-LIB-06 | **Erreurs** : `ExplorerError(message, code, status_code)`. `status_code` est le statut HTTP que l'app renverra. La bibliothèque lève ses sous-classes (`ColumnNotFound` avec suggestions, `NotNumericError`, `IngestionError`…). Dans l'app, `AppError` est un alias. |
| R-LIB-07 | **Données** : `dx.open(path, **options)` lit CSV, Parquet, Excel ou un dossier avec le lecteur de l'app (même détection du séparateur, des décimales, de l'encodage). Il écrit la copie Parquet dans un cache (`~/.cache/cyfouri-data-explorer/`, ou `cache_dir=`), réutilisée tant que la source ne change pas (même empreinte que l'app). `dx.from_pandas(df)` et `dx.from_arrow(table)` passent par le même cache. |
| R-LIB-08 | **Filtres** : `ds.where(column, op, values)` rend un nouveau `Dataset` qui partage le catalogue et ajoute une `Condition` (mêmes opérateurs que la barre de filtres). Les conditions se cumulent en ET. |
| R-LIB-09 | **Dépendances** : le cœur reprend celles de l'app sans FastAPI ni uvicorn (duckdb, pyarrow, numpy, scipy, statsmodels, scikit-learn, pydantic, openpyxl). Extras : `[ml]` (lightgbm, xgboost, optuna, cmaes), `[deep]` (torch). Aucune nouvelle dépendance. |
| R-LIB-10 | **Résultats** : les dataclasses existantes. Le paquet ajoute `to_dict()` (JSON-sérialisable, NaN → None) et `to_pandas()` sur les résultats tabulaires. |
| R-LIB-11 | **Version** `0.1.0`, Python ≥ 3.12. Pas de publication sur PyPI sans accord explicite. |

## Ordre de migration

Les tests restent verts à chaque étape, avec un commit par étape.

1. Paquet vide, branché à l'app (source uv), job CI « library ».
2. Déplacement du domaine pur (`app/domain/*` → paquet, imports réécrits) ; les services SQLite passent dans `app/services/`. Aucun changement de comportement.
3. Protocole `Catalog`, logique des colonnes, `Dataset`, `dx.open()`, `ds.types`, `ds.retype()`.
4. Variable, compare, corrélations, vue d'ensemble, lignes et filtres sur `Dataset`.
5. Rapport (`ds.report(path)`).
6. Séries temporelles, KPI, ML et synthétique (calcul d'un run dans le paquet).
7. README du paquet, notebook d'exemple, test de parité app ↔ bibliothèque, docs (ARCHITECTURE, PLAN, README).

## Critères d'acceptation

- GIVEN un environnement avec seulement le paquet (sans FastAPI) WHEN `import cyfouri_data_explorer` THEN aucune erreur, et `sys.modules` ne contient ni `fastapi` ni `sqlite3` importé par le paquet.
- GIVEN `samples/typing_traps.csv` WHEN `dx.open()` THEN `ds.types` donne les mêmes types, rôles et parseurs que la page Colonnes.
- GIVEN un dataset ouvert dans l'app et dans la bibliothèque WHEN on calcule `variable`, `compare`, `correlations` et `overview` THEN les résultats sont égaux champ par champ (test de parité).
- GIVEN une colonne mal tapée WHEN `ds.variable("Agee")` THEN `ColumnNotFound`, avec `"Age"` dans les suggestions.
- GIVEN `ds.retype("Pclass", "categorical_ordinal")` THEN `ds.compare("Pclass", "Survived")` traite Pclass comme une catégorie, comme dans l'app après correction.
- GIVEN `ds.where("Sex", "in", ["female"])` THEN le nombre de lignes et les statistiques portent sur les femmes seulement, et `ds` reste inchangé.
- GIVEN un second `dx.open()` du même fichier inchangé THEN la copie Parquet en cache est réutilisée.
- GIVEN `ds.report("out.html")` THEN le fichier est identique au rapport de l'app (hors date de génération).
- Les tests de l'app passent sans changement de comportement, et l'image Docker reste sous 900 Mo.

## Hors scope (phase 1)

- Les visuels (phase 2).
- `_repr_html_` dans Jupyter (après les visuels).
- La commande `dataexplorer app` et l'extra `[app]`.
- La publication sur PyPI et la documentation mkdocs.
