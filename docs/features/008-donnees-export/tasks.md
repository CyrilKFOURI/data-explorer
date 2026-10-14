# 008 — Données & export : tâches

## Backend
- [x] `domain/rows/` : vue (filtres, mode, recherche, tri), valeurs typées avec repli `{"invalid": brut}`, numéros de ligne, total en cache
- [x] Modes `first`, `sample` (10 000, reproductible), `duplicates` (regroupés), `missing`
- [x] Exports CSV / Parquet / Excel (limite de lignes), résumé statistique CSV (distincts exacts jusqu'à 200 000 valeurs)
- [x] API `GET /rows`, `GET /export`, `GET /export/summary` ; tests unitaires et API ; perf 5 M lignes (slow : bloc < 500 ms au début et à 4 M de profondeur, total < 1 s ; ordre toujours explicite, classement des seuls n° de ligne puis lecture de la page)

## Frontend
- [x] Dépendance `@tanstack/react-virtual` (validée par l'utilisateur)
- [x] Route `/d/$datasetId/data`, entrée Data active (surlignée même avec des paramètres d'URL) ; mode, recherche, tri dans l'URL
- [x] Table virtualisée par blocs de 100 : en-têtes (nom, icône de type, mini-histogramme, menu), cellules formatées, colonnes figées et masquées mémorisées
- [x] Menu d'export (format, colonnes visibles / toutes, Excel désactivé au-delà de la limite, résumé)
- [x] Tests : rendu et formats, chargement des blocs au défilement, tri, modes, recherche, masquer, export (6 tests)

## Docs & vérification
- [x] `docs/pages/07-donnees.md`, PLAN.md
- [x] Navigateur `typing_traps` : défilement, tri décroissant, colonne figée au défilement horizontal, exports CSV / Parquet / Excel / résumé (en-têtes et contenu vérifiés)
- [ ] Valeurs illisibles à l'œil : aucune dans les jeux d'exemple (types bien détectés) ; couvert par les tests unitaires et front
