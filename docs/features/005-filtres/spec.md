# 005 — Filtres globaux

## Objectif

Regarder le dataset **sur un sous-ensemble de lignes**, partout dans l'app, sans encombrer l'écran. Un bouton `Filter` dans la barre du haut ouvre un panneau ; les filtres actifs s'appliquent à toutes les pages du dataset (Vue d'ensemble, plein écran, fiche variable, Columns, et plus tard Compare, Correlations, Data). La donnée n'est jamais modifiée : les filtres deviennent une clause `WHERE` DuckDB à la lecture. Références : [00-transverse.md](../../pages/00-transverse.md), [DATES.md](../../DATES.md).

## Logique

- **Entre filtres : ET.** `country ∈ {FR}` + `age > 30` → les lignes qui vérifient les deux.
- **Dans un filtre catégoriel : OU** entre les valeurs cochées (`country ∈ {FR, BE}`).
- **« N'est pas »** sur chaque filtre (`∉`, `≠`, hors de l'intervalle, non vide…).
- Le OU entre colonnes différentes est hors V1 (mode avancé éventuel).
- **Unique values / Duplicates only** (ajout après la 008, à la demande de l'utilisateur) : sur une ou plusieurs colonnes. Ils s'appliquent **après** les filtres de valeurs, dans leur ordre d'ajout.

## User stories

1. Sur n'importe quelle page du dataset, le bouton `Filter` (raccourci `F`) ouvre un panneau : j'ajoute un filtre (colonne → condition → valeur), je modifie ou retire les filtres actifs, j'efface tout.
2. Le bouton affiche le nombre de filtres actifs et, à côté, `lignes filtrées / total`.
3. Le formulaire s'adapte au type : numérique (=, >, ≥, <, ≤, entre, vide) ; catégorie / booléen (cases à cocher avec recherche, tout cocher / décocher) ; texte / identifiant (contient, commence par, égal, vide) ; date (avant, après, entre, ou partie de date : année, mois, jour de semaine, heure).
4. Changer de page garde les filtres ; ils sont dans l'URL (rechargeable, partageable) et propres à chaque dataset.
5. Une ligne de puces sous la barre du haut est **optionnelle** (masquée par défaut, activable dans le panneau).
6. Depuis un graphique de carte, un clic sur une barre propose « Keep only » / « Exclude » ; sur un histogramme, « Keep this range ».
7. Depuis l'onglet Outliers, « Filter these rows » (garder les outliers) et « Exclude them ».
8. J'enregistre une combinaison sous un nom et je la réapplique en un clic ; je peux la supprimer.
9. Si aucun ligne ne reste, un état vide propose d'effacer les filtres.

## Critères d'acceptation

- GIVEN `typing_traps` et `country ∈ {FR}`, THEN le bandeau affiche les lignes FR / 600, et chaque carte, le plein écran et la fiche variable sont calculés sur ces lignes.
- GIVEN deux filtres, THEN ils se combinent en ET ; GIVEN deux valeurs cochées, THEN en OU.
- GIVEN « n'est pas » sur un intervalle numérique, THEN seules les lignes hors de l'intervalle restent (les vides sont exclus, comme en SQL).
- Le filtre porte sur la valeur **typée** de la colonne (son parser) : `price_eur > 100` compare des nombres, même si le fichier contient « 79,50 ».
- Filtre de date sur partie : `day_of_week ∈ {Mon}` ne garde que les lundis.
- Unique values : condition `{op: "unique", column, columns: [autres colonnes], keep: "first"|"last", order_by: colonne|null}`. GIVEN 3 lignes du véhicule V1 THEN une seule reste : la première du fichier (`keep=first`), la dernière (`keep=last`), ou celle de la date la plus récente (`keep=last, order_by=date`, vides en dernier, ex æquo départagés par l'ordre du fichier). Comparaison sur les valeurs **typées** ; les vides forment un groupe comme une valeur.
- Duplicates only : condition `{op: "duplicated", column, columns}` → les lignes dont la valeur (ou la combinaison) apparaît au moins deux fois, toutes les copies ; « n'est pas » → celles qui n'apparaissent qu'une fois.
- GIVEN `country ∈ {FR}` + unique sur `vehicle_id` (last) THEN la dernière ligne **FR** de chaque véhicule (filtres de valeurs d'abord).
- Le bandeau, les compteurs, toutes les pages et les exports en tiennent compte ; puce lisible (« vehicle_id · unique (last by date) »).
- Valeurs injectées échappées ; colonne inconnue, opérateur incompatible avec le type ou valeur illisible → erreur 422 claire.
- Columns : types et détection inchangés par les filtres ; les résumés (vides, distinctes, exemples, mini-histogramme) sont recalculés sur les lignes filtrées.
- Filtres enregistrés persistés en SQLite par dataset ; supprimés avec le dataset.
- Performance : sur 5 M lignes, un filtre simple ajoute moins d'une seconde à la Vue d'ensemble.

## Hors scope

OU entre colonnes différentes, filtres relatifs (« 12 derniers mois »), sélection lasso sur un nuage de points (006).
