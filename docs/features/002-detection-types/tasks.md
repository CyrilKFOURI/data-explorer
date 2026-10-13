# 002 — Détection des types : tâches

## Backend
- [x] `domain/typing/types.py` : types d'analyse, confiance, `Parser`, `ColumnDetection`
- [x] Base de connaissances TOML (`roles.toml`, `vocabulary.toml`) + chargeur, normalisation des noms, correspondance des rôles
- [x] `parsers.py` : expressions SQL (nombres FR/EN, dates, booléens, années, texte, valeurs nulles)
- [x] `engine.py` : échantillon reproductible, profils, règles ordonnées avec raisons et confiance, candidats par famille
- [x] `summary.py` : résumé sur toutes les lignes (vides, invalides, distinctes, exemples, histogramme)
- [x] `conversion.py` : parseur adapté quand l'utilisateur change de type
- [x] Migration `0003_columns` + `datasets.types_reviewed_at`
- [x] `domain/columns/` : dépôt + service (détection après import, détection paresseuse, corrections, réinitialisation, ordre, exclusion, aperçu de conversion, validation, `types_version`)
- [x] API : `GET/PATCH /datasets/{id}/columns`, `POST …/columns/detect`, `GET …/columns/conversion`, `POST …/columns/review`, `GET /column-roles`
- [x] Tests : jeu de référence 100 % (`typing_traps`, `sales_timeseries`), dates ambiguës, identifiants répétés, rôles, parseurs, API

## Frontend
- [x] Client + hooks (colonnes, rôles, corrections écrites dans le cache)
- [x] `TypeBadge` (menu Radix avec raisons et descriptions des types), `Sparkline`, `OrderDialog`
- [x] Page `/d/:id/columns` : tri par confiance, filtres (à revoir, exclues, par type), recherche, sélection multiple, annulation (bouton + Ctrl+Z), alerte de valeurs illisibles, validation
- [x] Barre latérale : « Columns » actif quand un dataset est ouvert ; import → page Columns si types non validés
- [x] Tests : page Columns (rôle + annulation, type via menu, exclusion multiple, filtres, validation), parcours d'import mis à jour

## Vérification
- [x] Navigateur : détection sur `typing_traps` (21/21) et `sales_timeseries`, correction de type avec alerte, Ctrl+Z, validation
- [x] Performance : détection + résumés de 1 M lignes × 8 colonnes en 1,6 s
