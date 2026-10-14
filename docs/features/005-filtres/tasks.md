# 005 — Filtres globaux : tâches

## Backend
- [x] `domain/filters/model.py` : `Condition` (colonne, op, valeurs, partie de date, négation)
- [x] `domain/filters/sql.py` : condition → SQL sur la valeur typée, validation par type, échappement
- [x] Paramètre `filters` (JSON) sur overview, chart, variable, fit, outliers ; caches par filtre
- [x] Vue d'ensemble filtrée : lignes filtrées + total, vides / distinctes recalculés
- [x] `GET /datasets/{id}/columns/summaries?filters=` : résumés des colonnes sur les lignes filtrées
- [x] Filtres enregistrés : migration 0004, `GET/POST/DELETE /datasets/{id}/saved-filters`
- [x] Tests : compilation par type, ET / OU / négation, parties de date, injection, erreurs 422, API filtrée, perf 5 M (distinctes approchées au-delà de 200 000 lignes filtrées ; échantillon tiré une seule fois par analyse)

## Frontend
- [x] État des filtres dans l'URL (`?filters=`), conservé entre les pages, propre au dataset
- [x] Hooks de données : filtres dans les requêtes et les clés de cache
- [x] Bouton `Filter` (compteur + lignes filtrées / total) dans la barre du haut, raccourci `F`
- [x] Panneau : liste, ajout, édition, suppression, tout effacer ; éditeurs par type ; puces optionnelles
- [x] Clic sur un graphique (cartes, fiche variable) → Keep only / Exclude / Keep this range ; pas dans le plein écran (le menu y serait mal placé dans la fenêtre modale)
- [x] Outliers → Filter these rows / Exclude them
- [x] Filtres enregistrés : enregistrer, appliquer, supprimer
- [x] État vide « 0 ligne » avec « Clear filters » ; Columns sur lignes filtrées
- [x] Tests : conditions, URL, clic graphique, parcours (ajout, navigation, autre dataset, retrait), outliers (55 tests frontend)

## Unique values / Duplicates only (ajout)
- [x] Modèle : opérateurs `unique` / `duplicated`, `columns`, `keep`, `order_by` ; validation (colonnes connues et non ignorées)
- [x] SQL : filtres de valeurs puis fenêtres (`row_number` / `count`) dans l'ordre d'ajout ; partout via `scoped_source`
- [x] Tests backend : first / last / ordered by, combinaison de colonnes, duplicates et sa négation, après un filtre de valeurs, API (vue d'ensemble, lignes)
- [x] Front : choix dans l'éditeur, « Based on : This column / Several columns (key) » (cases à cocher, au moins une colonne de plus exigée), keep, ordered by ; puce ; tests
- [x] Vérification navigateur : `sales_timeseries`, store · unique (last by date) → 3 / 3 285 lignes, une par magasin au 2024-12-30

## Vérification
- [x] Navigateur : `typing_traps`, FR (175/600) + âge ≥ 60 (67) + lundi (5), navigation Overview → Columns → fiche, enregistrement, rechargement, puces, Clear all
- [ ] Clic sur un graphique vérifié à l'œil (panneau navigateur masqué : couvert par les tests)
- [x] Clé à plusieurs colonnes vérifiée à l'œil : store + promo · unique (first) → 6 / 3 285 lignes
