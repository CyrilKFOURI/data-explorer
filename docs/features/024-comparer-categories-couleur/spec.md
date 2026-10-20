# 024 — Comparer : nombres discrets comme catégories, couleur sur les groupes

Page : [05-comparer.md](../../pages/05-comparer.md). Prolonge la [006](../006-comparer/spec.md).

## Objectif

Sur Titanic, « Survived × Age, couleur Sex » doit donner des boîtes à moustaches d'âge pour chaque valeur de Survived, une boîte par sexe. Aujourd'hui, ça ne marche pas, pour deux raisons :
- Pclass (1–3), SibSp, Parch sont des **nombres discrets** : Compare les croise comme des nombres et trace un nuage de points inutile (Survived, lui, est détecté comme booléen) ;
- la **couleur** n'existe que pour le nuage de points et la série temporelle : le graphique en groupes l'ignore.

## User stories

1. Je choisis Pclass en X et Age en Y. Pclass, qui n'a que 3 valeurs, est lu comme une catégorie : je vois trois boîtes à moustaches et l'ANOVA, avec la mention « Pclass: 3 values, read as categories ».
2. Si je préfère les nombres, je clique « As numbers » à côté du sélecteur, et le nuage de points revient.
3. J'ajoute Sex en couleur : pour chaque valeur de Survived, une boîte par sexe côte à côte, avec une légende. Ça marche aussi en violons et en moyennes avec intervalle de confiance.
4. Une colonne de couleur qui a trop de modalités est grisée dans la liste, avec sa raison (« 14 values: at most 6 »).

## Règles

| Id | Règle |
|---|---|
| R-CMP-01 | Un **nombre discret** avec **au plus 12 valeurs distinctes** est lu comme une catégorie dans Compare, par défaut. Ses valeurs sont triées dans l'ordre numérique et écrites sans décimales inutiles (« 1 », pas « 1.0 »). |
| R-CMP-02 | « As numbers » (dans l'URL : `numbers=Survived,Pclass`) garde la lecture en nombres pour les colonnes listées. Au-delà de 12 valeurs, la colonne reste un nombre. |
| R-CMP-03 | La **couleur** est permise pour nombre × nombre, date × nombre (comme avant) et nombre × catégorie (nouveau). Elle exige une catégorie, ou un nombre discret lu comme catégorie (R-CMP-01). |
| R-CMP-04 | **Au plus 6 modalités de couleur** pour les groupes : au-delà, la colonne est grisée dans la liste avec sa raison, et l'API répond par une erreur claire. Pour le nuage de points et la série temporelle, les 8 plus fréquentes restent, comme avant. |
| R-CMP-05 | Avec une couleur, l'axe des groupes garde **ses 8 catégories les plus fréquentes**, le reste en « Others » : au plus 8 × 6 = 48 boîtes. |
| R-CMP-06 | Les **tests** comparent toujours les groupes de l'axe, toutes couleurs confondues. Une note le dit (« Tests compare the Survived groups, all Sex values together »). |

## Données et API

- `GET /datasets/{id}/compare` accepte `numbers` (colonnes à garder en nombres, séparées par des virgules).
- La réponse porte `categories` : les colonnes lues comme catégories par R-CMP-01, chacune avec son nombre de valeurs.
- `Group` porte `color` : la modalité de couleur de la boîte, ou null sans couleur.

## Critères d'acceptation

- GIVEN Titanic WHEN X = Pclass, Y = Age THEN le visuel est en groupes (boîtes), avec 3 groupes « 1 », « 2 », « 3 » dans cet ordre, une ANOVA, et `categories` contient Pclass.
- GIVEN `numbers=Pclass` THEN le visuel redevient un nuage de points.
- GIVEN X = Survived, Y = Age, couleur = Sex THEN il y a 4 groupes (False et True, chacun pour female et male), chacun avec son effectif et ses quartiles, et une boîte par couleur sur le graphique.
- GIVEN une couleur de plus de 6 modalités sur des groupes THEN erreur « Color has N values: pick one with at most 6 », et la colonne est grisée dans la liste.
- GIVEN Pclass (3 valeurs) × Survived (2 valeurs) THEN le visuel est un tableau croisé (deux catégories).
- GIVEN un nombre discret de 50 valeurs THEN il reste un nombre.
