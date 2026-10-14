# 008 — Données & export

## Objectif

Voir les **lignes** du dataset après les filtres globaux, comme point de contrôle, et les **exporter**. Référence : [07-donnees.md](../../pages/07-donnees.md).

## User stories

1. Sur `/d/:id/data`, je fais défiler toutes les lignes filtrées, même plusieurs millions, sans ralentissement : la table est virtualisée et charge les lignes par blocs.
2. Chaque en-tête montre le nom, le badge de type et un mini-histogramme. Un clic sur le nom trie (croissant → décroissant → ordre du fichier). Un menu propose : trier, filtrer sur cette colonne, masquer, figer à gauche, ouvrir la fiche variable.
3. Les cellules sont lisibles : nombres alignés à droite au format de la locale, dates lisibles, booléens, vides en « — » grisé, texte long tronqué avec info-bulle. Une valeur que le type choisi ne sait pas lire est affichée brute, en italique, signalée.
4. Je choisis un **mode d'affichage** : premières lignes · échantillon aléatoire · doublons seulement · lignes avec manquants seulement.
5. Je **cherche** un texte dans toutes les colonnes visibles du sous-ensemble.
6. J'**exporte** ce que je vois (filtres, mode, recherche, tri) en CSV, Parquet ou Excel, avec les colonnes visibles ou toutes ; j'exporte aussi le **résumé statistique** de toutes les colonnes en CSV.

## Critères d'acceptation

- API `GET /datasets/{id}/rows?offset&limit&mode&search&sort&desc&filters` → `{columns, rows, total, offset}` ; `limit` ≤ 500 ; chaque ligne commence par son numéro dans le fichier (à partir de 1).
- Valeurs lues dans le type effectif de chaque colonne (même parseur que les analyses) ; si la lecture échoue alors que la valeur brute existe, la valeur brute est renvoyée (texte) ; les colonnes ignorées sont renvoyées brutes.
- Modes :
  - `first` : ordre du fichier (ou le tri choisi) ;
  - `sample` : **échantillon reproductible** de 10 000 lignes au plus (`hash(n° de ligne + 42)`), dans l'ordre du fichier ;
  - `duplicates` : lignes dont toutes les valeurs brutes apparaissent au moins deux fois, regroupées (les copies se suivent) ;
  - `missing` : lignes avec au moins une valeur manquante (vide ou nulle) dans une colonne non ignorée.
- GIVEN un CSV avec 2 lignes identiques WHEN mode = duplicates THEN ces 2 lignes, côte à côte ; GIVEN une valeur vide THEN la ligne apparaît en mode missing.
- Recherche : sous-chaîne insensible à la casse dans le texte de chaque colonne non ignorée ; combinée aux filtres et au mode.
- Tri : une colonne, valeurs typées, vides en dernier, ex æquo dans l'ordre du fichier.
- `total` = nombre de lignes de la vue (après filtres, mode, recherche) ; mis en cache par (dataset, types, filtres, mode, recherche).
- Export `GET /datasets/{id}/export?format=csv|parquet|xlsx&columns&mode&search&sort&desc&filters` → fichier téléchargé, nommé `<dataset>-<date>.<ext>` ; valeurs typées (nombres en nombres, dates en dates).
  - Excel : au plus 1 048 575 lignes, sinon erreur 422 `too_many_rows` qui propose CSV ou Parquet.
- Export du résumé : `GET /datasets/{id}/export/summary` → CSV, une ligne par colonne (type, lignes, manquants, distincts, min, max, moyenne, écart-type, médiane… selon le type), sur les lignes filtrées.
- Performance : 5 M lignes → un bloc de 100 lignes en moins de 500 ms, au début comme à 4 M de profondeur, le nombre total en moins de 1 s. L'ordre est toujours explicite (`ORDER BY` n° de ligne) : sans lui, DuckDB rend les lignes d'un gros Parquet dans le désordre ; la page classe d'abord les seuls numéros de ligne, puis lit ces lignes.
- Front :
  - colonnes masquées et figées mémorisées par dataset (stockage local) ; « N of M columns » pour les réafficher ;
  - le tri, le mode et la recherche vivent dans l'URL (partageables, conservés au retour) ;
  - aucune ligne → message `NoRows` (avec effacement des filtres) ou « aucune ligne ne correspond à la recherche ».

## Hors scope

Édition des cellules, export du rapport HTML complet (plus tard), tri multi-colonnes, redimensionnement des colonnes à la souris.
