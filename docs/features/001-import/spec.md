# 001 — Import

## Objectif

Faire entrer des données dans l'app : un fichier ou un dossier (CSV, TSV, Parquet, Excel) devient un **dataset** stocké en Parquet dans le workspace, retrouvable dans la liste des datasets récents. Page de référence : [01-accueil-import.md](../../pages/01-accueil-import.md).

La détection des types (002) et les pages d'analyse (003+) viennent ensuite. En attendant, un dataset importé ouvre une **page de résumé provisoire** (`/d/:id`) : taille, colonnes et types de stockage, premières lignes.

## User stories

1. Je glisse-dépose un fichier sur l'accueil (ou je clique « Choose file ») et j'arrive sur un aperçu.
2. Je parcours un dossier (le dossier monté `/data` en Docker, n'importe quel dossier en natif) et je choisis un fichier ou un dossier entier ; en natif, je peux aussi coller un chemin.
3. Dans l'aperçu, je vois le format détecté, les 20 premières lignes et une estimation du nombre de lignes. Je peux corriger les réglages CSV (séparateur, encodage, en-tête, séparateur décimal), choisir les feuilles Excel, les fichiers d'un dossier, les colonnes à garder, un échantillon en %, et le nom du dataset.
4. Je lance l'import et je vois sa progression ; à la fin, j'arrive sur le dataset.
5. Sur l'accueil, je retrouve mes datasets récents : ouvrir, renommer, réimporter, supprimer. Un dataset dont la source a changé est signalé.
6. Je peux essayer l'app avec un jeu de démo en un clic.

## Critères d'acceptation

**Aperçu**
- GIVEN un CSV `;`-séparé avec décimales `,`, WHEN je demande l'aperçu, THEN séparateur `;`, décimale `,`, en-tête détecté, et les 20 premières lignes sont renvoyées.
- GIVEN un CSV en latin-1, WHEN je demande l'aperçu, THEN l'encodage proposé est `latin-1` et les accents sont lisibles.
- GIVEN un fichier Excel à plusieurs feuilles, THEN la liste des feuilles est renvoyée et la première est prévisualisée.
- GIVEN un dossier, THEN les fichiers pris en charge sont listés (les autres ignorés), et un avertissement apparaît si leurs colonnes diffèrent.
- GIVEN un fichier vide, protégé ou illisible, THEN un message d'erreur clair est renvoyé (pas de trace technique).

**Import**
- GIVEN un aperçu validé, WHEN je lance l'import, THEN un job est créé, sa progression est consultable, et à la fin le dataset passe à `ready` avec `row_count`, `col_count`, `size_bytes` et une copie `datasets/<id>/data.parquet`.
- GIVEN une sélection de colonnes, THEN seules ces colonnes sont dans la copie.
- GIVEN un échantillon de x %, THEN la copie contient environ x % des lignes, et deux imports identiques donnent exactement les mêmes lignes (graine fixe).
- GIVEN un dossier, THEN tous les fichiers cochés sont empilés (union des colonnes ou intersection, au choix), avec une colonne `source_file`.
- GIVEN une source déjà importée avec les mêmes options et inchangée, WHEN je l'importe à nouveau, THEN le dataset existant est renvoyé immédiatement, sans relecture.
- GIVEN une erreur pendant l'import, THEN le dataset passe à `error` avec un message lisible.

**Datasets récents**
- GIVEN des datasets, THEN la liste est triée par dernière ouverture, avec statut, taille, lignes × colonnes.
- GIVEN un fichier source modifié ou supprimé après l'import, THEN le dataset est marqué « source changed » ou « source missing ».
- WHEN je renomme, réimporte ou supprime un dataset, THEN l'action est appliquée ; la suppression efface la copie et le cache, **jamais la source** (sauf un fichier uploadé, qui est une copie interne).

**Sécurité**
- GIVEN un dossier de données restreint (`DATA_EXPLORER_DATA_DIR`, ex. `/data` en Docker), WHEN un chemin hors de ce dossier est demandé (y compris via `..`), THEN la requête est refusée.

## Hors scope

Détection des types et page Colonnes (002), import depuis une URL ou une base SQL, rafraîchissement automatique. Jeux de démo publics (Titanic, Iris…) : ajoutés quand leur téléchargement est validé ; cette feature fournit deux jeux synthétiques (`typing_traps`, `sales_timeseries`) et le script du gros volume.
