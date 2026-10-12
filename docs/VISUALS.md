# Visuels et règles d'affichage

Bibliothèque : **Plotly** (plotly.js côté interface). Tous les graphiques passent par la même couche (`frontend/src/charts/`). Elle applique le thème, les règles ci-dessous et les actions communes.

## Règles générales (tous les graphiques)

- **Une carte = un graphique** avec, en en-tête : le nom de la colonne, un badge de type (cliquable pour le changer) et des actions : plein écran, changer de visuel, télécharger (PNG/SVG), copier les données (CSV), ouvrir dans Comparer.
- **Échantillonnage visible** : au-delà de 50 000 points (seuil réglable), les nuages de points sont dessinés sur un échantillon aléatoire à graine fixe. La mention « échantillon de 50 000 / 2,3 M lignes » s'affiche toujours. Les statistiques, elles, sont calculées sur toutes les lignes.
- **Grands volumes** : densité 2D ou hexbin à la place d'un nuage de points si l'échantillon reste illisible.
- **États vides explicites** : un message (« Aucune ligne après filtres », « Choisissez une variable Y ») plutôt qu'un graphique vide ou une erreur.
- **Nombres** au format français (1 234,5 ; 1,2 M), axes en % pour les rôles pourcentage, unités issues du rôle sémantique.
- **Couleurs** : palette catégorielle validée (skill `dataviz`), lisible en clair et en sombre. Une même catégorie garde la même couleur partout dans la session.

## Règles d'affichage des variables catégorielles

| Règle | Comportement |
|---|---|
| **Top N** | Seules les N modalités les plus fréquentes sont affichées. N = 10 par défaut, réglable de 5 à 50 (curseur sur la carte, défaut global dans Paramètres). |
| **« Autres »** | Le reste est regroupé en une barre « Autres (37 modalités, 12,4 %) », distincte visuellement (gris). |
| **Manquants** | Barre séparée « (manquant) », jamais mélangée à « Autres ». |
| **Plein écran** | Le bouton plein écran affiche **toutes** les modalités : barres défilantes, champ de recherche, tableau effectifs / % / % cumulé. Au-delà de 1 000 modalités : tableau virtualisé seulement, pas de barres. |
| **Orientation** | Barres **horizontales** dès que les libellés sont longs (> 12 caractères) ou au-delà de 8 modalités. Libellés tronqués avec « … », texte complet au survol. |
| **Tri** | Par fréquence (défaut), alphabétique, ou ordre naturel pour un ordinal. |
| **Camembert** | Proposé seulement si ≤ 5 modalités, jamais par défaut. |
| **Forte cardinalité** | Si distinctes / lignes > 50 % : pas de barres. On affiche le nombre de distinctes, des exemples, et une suggestion (« Ressemble à un identifiant ou à du texte libre — changer le type ? »). |
| **Numérique discret** | Mêmes règles que le catégoriel, mais les barres restent dans l'ordre numérique (1, 2, 3…) et aucune valeur n'est regroupée dans « Autres » tant qu'il y a ≤ 20 valeurs. |

## Mise en page des grilles (Vue d'ensemble)

- **3 graphiques par ligne** sur un écran large, 2 sur une fenêtre moyenne, 1 sur une fenêtre étroite.
- **Pagination** : 12 variables par page (4 lignes) par défaut, réglable à 6, 12, 24 ou 48. On défile verticalement dans la page, on change de page en bas et en haut.
- Les graphiques hors de l'écran ne sont pas rendus avant d'être visibles, pour garder la fluidité sur 200 colonnes.

## Choisir un visuel selon l'intention

Sur la page Comparer, l'utilisateur peut choisir **ce qu'il veut voir** au lieu d'un type de graphique. L'app propose alors les visuels compatibles avec les types des colonnes choisies.

| Intention | Visuels proposés |
|---|---|
| Distribution | Histogramme, KDE, ECDF, boîte, violon, raincloud, QQ-plot, ridgeline (par groupe) |
| Comparer des groupes | Boîtes / violons par groupe, barres de moyenne avec intervalle de confiance, strip plot, ridgeline |
| Relation | Nuage de points (+ régression / LOWESS), hexbin, densité 2D, contours, matrice de nuages (SPLOM) |
| Composition | Barres empilées à 100 %, treemap, sunburst, mosaïque, parallel categories |
| Profils multivariés | Coordonnées parallèles, radar par groupe, heatmap normalisée |
| Évolution | Ligne, aire, volume par période (le reste vient avec le module séries temporelles) |

## Catalogue par combinaison de types

| Combinaison | Visuels 2D | Visuels 3D / originaux |
|---|---|---|
| 1 numérique | Histogramme, KDE, ECDF, boîte, violon, QQ-plot | — |
| 1 catégoriel ou discret | Barres Top N, barre 100 % | Treemap |
| 1 date | Volume par période (pas auto : jour → semaine → mois → trimestre → année) | Heatmap calendrier |
| num × num | Nuage, hexbin, densité 2D, contours | — |
| num × cat | Boîtes, violons, raincloud, barres de moyenne ± IC, ridgeline | — |
| cat × cat | Heatmap de contingence, barres empilées / groupées, mosaïque | Parallel categories |
| num × num × num | Nuage coloré par la 3ᵉ | **Nuage 3D**, **surface de densité 3D** |
| num × num × cat | Nuage coloré par groupe, contours par groupe | **Nuage 3D** (axe Z = 3ᵉ numérique optionnel) |
| n numériques | SPLOM, coordonnées parallèles, heatmap de corrélation | **Nuage 3D sur projection ACP** |
| lat × lon | Carte de points, carte de densité (tuiles hors-ligne à prévoir) | — |

## Ajouter un visuel

Un visuel = un fichier dans `frontend/src/charts/builders/` qui déclare : son identifiant, les types d'entrée acceptés, les intentions couvertes, et une fonction données → traces Plotly. Le registre (`charts/registry.ts`) le propose automatiquement partout où il est compatible. Si le visuel a besoin de données préparées (bins, KDE, contingence…), on ajoute la préparation côté backend dans `domain/charts/`.
