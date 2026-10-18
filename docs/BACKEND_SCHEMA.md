# Backend Schema

> Statut : proposition. Base **SQLite** (`workspace/app.db`) pour les métadonnées ; les données elles-mêmes sont dans des fichiers **Parquet** lus par DuckDB.

## Entités / tables

### V1

| Table | Rôle | Colonnes principales |
|---|---|---|
| `datasets` | Un jeu de données importé | `id`, `name`, `source_path`, `source_kind` (file/folder), `format` (csv/parquet/excel/mixed), `options` (JSON des options d'import), `fingerprint`, `storage_path`, `row_count`, `col_count`, `size_bytes`, `sample_pct`, `status` (importing / ready / error), `error`, `created_at`, `imported_at`, `last_opened_at`, `types_version`. L'état de la source (ok / changed / missing) n'est pas stocké : il est calculé en comparant `dataset_files` aux fichiers actuels |
| `dataset_files` | Fichiers sources d'un dataset importé depuis un dossier | `dataset_id`, `path`, `size`, `mtime`, `row_count` |
| `columns` | Une colonne : détection, corrections, résumé | `dataset_id`, `name`, `position`, `storage_dtype`, `detected_type`, `detected_role`, `detected_parser` (JSON), `detected_order` (JSON), `candidates` (meilleur parseur par famille, JSON), `confidence`, `reasons` (JSON), `user_type`, `user_role` (`''` = aucun rôle), `user_parser`, `user_order`, `excluded`, `summary` (JSON : lignes, vides, invalides, distinctes, exemples, histogramme). `datasets` gagne `types_reviewed_at` |
| `saved_filters` | Filtres enregistrés (migration 0004) | `id`, `dataset_id`, `name` (unique par dataset : réenregistrer remplace), `conditions` (JSON : liste de conditions combinées en ET), `created_at`. Les filtres **actifs** ne sont pas stockés : ils vivent dans l'URL (`?filters=`) |
| `ui_state` | Où l'utilisateur en était, par dataset | `dataset_id`, `key` (ex. `overview.page`, `overview.topN`), `value` (JSON) |
| `settings` | Préférences globales du serveur : clé `detection` = seuils de détection (`parse_rate`, `empty_rate`, `discrete_max`, `identifier_unique`). Apparence et valeurs par défaut de l'analyse restent dans le navigateur | `key`, `value` (JSON) |
| `analysis_cache` | Index du cache des analyses | `key` (hash), `dataset_id`, `analysis`, `params_hash`, `result` (JSON ou chemin de fichier), `size_bytes`, `created_at`, `last_used_at` |
| `jobs` | Tâches longues | `id`, `kind`, `dataset_id`, `status` (pending / running / done / failed), `progress` (0–1), `message`, `created_at`, `finished_at`. Au démarrage, les jobs restés en cours sont marqués en échec |

### Modules futurs (ajoutés par migration au sprint concerné)

| Table | Module |
|---|---|
| `ts_configs` (colonne de temps, fréquence, série) | Séries temporelles |
| `ml_runs` (migration 0005 : dataset, cible, problème, modèle, réglages, filtres, score principal, durée ; résultat JSON et pipeline `joblib` dans `datasets/<id>/ml/`, supprimés avec le dataset) | Machine learning (016) |
| `kpi_definitions` | Builder KPI |
| `synthetic_runs` (méthode, paramètres, scores de fidélité, chemin du dataset généré) | Données synthétiques |

## Relations

```
datasets 1──n dataset_files
datasets 1──n columns
datasets 1──n saved_filters
datasets 1──n ui_state
datasets 1──n analysis_cache
datasets 1──n jobs
(futur) datasets 1──n ml_experiments 1──n ml_runs
(futur) datasets 1──n synthetic_runs ──▶ produit un nouveau dataset (datasets.id)
```

- **Type effectif** d'une colonne = `user_type` s'il est renseigné, sinon `detected_type`. Même règle pour le rôle.
- Toute correction de type incrémente `datasets.types_version`, ce qui change les clés de cache : les analyses concernées sont recalculées.
- Supprimer un dataset supprime ses lignes liées, sa copie Parquet et son cache. La source n'est jamais touchée.

## Règles d'accès (qui lit/écrit quoi)

- Application **mono-utilisateur locale** (validé) : pas de notion d'utilisateur ni de droits.
- **Seul le backend** lit et écrit SQLite et le workspace. Le frontend passe toujours par l'API.
- Les **fichiers sources** sont en lecture seule.
- Le cache peut être vidé à tout moment (Paramètres) sans perte d'information : il se reconstruit.
