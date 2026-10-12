# 001 — Import : tâches

## Backend
- [x] Dépendances : duckdb, polars, pyarrow, openpyxl
- [x] Migration `0002_datasets` : tables `datasets`, `dataset_files`, `jobs`
- [x] `domain/ingestion/` : formats et dossiers (`sources.py`), détection CSV (`csv_sniff.py`), lecture unifiée DuckDB (`reader.py`), aperçu (`preview.py`), import Parquet (`importer.py`), navigation (`browse.py`), messages d'erreur lisibles (`errors.py`)
- [x] `core/jobs.py` : tâches en arrière-plan (threads) + exécution immédiate pour les tests ; reprise après redémarrage (jobs interrompus → échec)
- [x] `domain/datasets/` : dépôt SQLite + service (import, réutilisation par empreinte, réimport, état de la source, renommage, suppression, schéma, premières lignes, uploads)
- [x] API : `/datasets` (CRUD, reimport, open, schema, head), `/sources/preview`, `/browse`, `/samples`, `PUT /uploads` (corps brut, sans multipart), `/jobs/{id}`
- [x] Restriction au dossier de données (`DATA_EXPLORER_DATA_DIR`)
- [x] Tests : 20 tests d'ingestion + 14 tests d'API

## Frontend
- [x] Client API typé + hooks (sondage des jobs et des imports en cours)
- [x] Primitives UI : Button, Dialog (Radix), champs, barre de progression
- [x] Accueil : zone de dépôt, choix de fichier, « Browse », jeux de démo, datasets récents (renommer, réimporter, supprimer avec confirmation, statut)
- [x] Dialogue d'aperçu : réglages CSV, feuilles Excel, fichiers d'un dossier (union/intersection), exclusion de colonnes, échantillon, nom, progression
- [x] Page provisoire `/d/:id` : résumé, premières lignes, colonnes ; nom du dataset dans la barre du haut
- [x] Tests : parcours d'import complet, erreurs, liste des datasets, formatage

## Données de démo et outillage
- [x] `scripts/make_samples.py` → `samples/typing_traps.csv`, `samples/sales_timeseries.csv`
- [x] `scripts/make_big_sample.py` → `data/big_sample.parquet` (~5 M lignes, non commité)
- [x] Docker : jeux de démo dans l'image, `/data` comme dossier restreint
- [x] Vérifié dans le navigateur : aperçu, import, page dataset, liste, « Browse »
- [ ] Jeux publics (Titanic, Iris, Penguins, California Housing) : téléchargement à valider
