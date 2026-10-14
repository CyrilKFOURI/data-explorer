# Éléments transverses

Présents sur toutes les pages d'un dataset (`/d/:id/...`).

## Barre latérale (gauche, repliable)

- **Dataset** : Colonnes · Vue d'ensemble · Comparer · Corrélations · Données
- **Modules** : vide en V1 ; les modules activés s'y ajoutent automatiquement (Séries temporelles, ML…)
- En bas : Paramètres, bascule clair / sombre

## Barre du haut

- Nom du dataset (renommable) + sélecteur pour changer de dataset
- Recherche / palette de commandes (⌘K ou Ctrl+K) : aller à une variable, une page, une action (« Exporter », « Effacer les filtres »)

## Bandeau de résumé

Toujours visible, et il tient compte des filtres actifs.

| Indicateur | Détail au survol |
|---|---|
| Lignes | Après filtres / total |
| Colonnes | Dont ignorées |
| Manquants | % de cellules vides ; clic → colonnes triées par % de manquants |
| Lignes dupliquées | Nombre et % |
| Colonnes dupliquées | Colonnes identiques en contenu (pas seulement en nom) |
| Mémoire | Taille totale, moyenne par ligne |
| Types | Mini-barre de répartition : numérique / catégoriel / date / booléen / texte / identifiant |

## Filtres globaux

Discrets par défaut : un **bouton `Filter`** dans la barre du haut (raccourci `F`), présent sur toutes les pages du dataset.

- Le bouton affiche le nombre de filtres actifs ; à côté, « 12 340 / 1 200 000 lignes » dès qu'un filtre est actif.
- Un clic ouvre un **panneau** : filtres actifs (modifier, retirer), **+ Add filter** (colonne → condition → valeur), « Clear all ». Le formulaire s'adapte au type :
  - numérique : =, >, ≥, <, ≤, entre, est vide
  - catégoriel / booléen : est parmi (cases à cocher avec recherche, tout cocher / décocher)
  - texte / identifiant : contient, commence par, égal, est vide
  - date : avant, après, entre, ou partie de date (année, mois, jour de semaine, heure)
  - chaque filtre a une option « n'est pas »
  - toute colonne (hors ignorée) propose aussi **Unique values** (une ligne par valeur : garder la première ou la dernière, selon l'ordre du fichier ou « ordered by » une colonne, ex. la date la plus récente) et **Duplicates only** (les lignes dont la valeur apparaît au moins deux fois ; « n'est pas » = valeurs présentes une seule fois). « + column » ajoute des colonnes : l'unicité porte alors sur la combinaison (ex. `vehicle_id` + `month`)
- Logique : **ET entre les filtres**, **OU entre les valeurs cochées** d'un même filtre. Le OU entre colonnes différentes est hors V1. Les filtres de valeurs s'appliquent d'abord, puis Unique / Duplicates, dans l'ordre où ils ont été ajoutés.
- **Puces** sous la barre du haut (`pays ∈ {FR, BE}` ✕) : optionnelles, masquées par défaut, activables dans le panneau.
- Filtres **enregistrables** sous un nom et réutilisables.
- Raccourcis : clic sur une barre d'un graphique → « Keep only » / « Exclude » ; plage d'histogramme → « Keep this range » ; onglet Outliers → « Filter these rows » / « Exclude them ».
- Les filtres suivent la navigation entre les pages, sont dans l'URL et propres à chaque dataset.

## Comportements communs

- L'URL contient la page, la variable et les filtres : partageable, rechargeable.
- Squelettes de chargement à la forme du contenu ; erreurs expliquées (« Ce fichier Excel est protégé par mot de passe »).
- Notifications discrètes en bas à droite pour les tâches longues (import, recalcul).
