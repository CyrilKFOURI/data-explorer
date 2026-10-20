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
4. Si la couleur a beaucoup de valeurs (Cabin, Embarked…), la page met automatiquement la catégorie qui en a le plus sur l'axe et réduit l'ensemble à 15 boîtes au plus, en disant ce qu'elle a fait.

## Règles

| Id | Règle |
|---|---|
| R-CMP-01 | Un **nombre discret** avec **au plus 12 valeurs distinctes** est lu comme une catégorie dans Compare, par défaut. Ses valeurs sont triées dans l'ordre numérique et écrites sans décimales inutiles (« 1 », pas « 1.0 »). |
| R-CMP-02 | « As numbers » (dans l'URL : `numbers=Survived,Pclass`) garde la lecture en nombres pour les colonnes listées. Au-delà de 12 valeurs, la colonne reste un nombre. |
| R-CMP-03 | La **couleur** est permise pour nombre × nombre, date × nombre (comme avant) et nombre × catégorie (nouveau). Elle exige une catégorie, ou un nombre discret lu comme catégorie (R-CMP-01). |
| R-CMP-04 | **Disposition (révisée le 2026-10-20).** Avec un nombre et deux catégories, la place choisie (X, Y ou couleur) ne compte pas, c'est le même problème. **La catégorie qui a le plus de valeurs va sur l'axe des groupes, l'autre en couleur.** Si la couleur choisie a plus de 5 valeurs et en a plus que l'autre catégorie, les deux sont échangées automatiquement, et la page le dit. |
| R-CMP-05 | **Au plus 15 boîtes au total**, soit (valeurs de l'axe) × (valeurs de la couleur), « Others » compris. **Au plus 5 couleurs**. Au-delà, les valeurs les moins fréquentes passent en « Others » : d'abord la couleur (au plus 5), puis l'axe (au plus ⌊15 / couleurs⌋). Exemple : 10 et 7 valeurs donnent 10 sur l'axe et 7 en couleur, réduites à 4 couleurs + « Others » × 2 groupes + « Others », soit 15 boîtes. Sans couleur, au plus 15 groupes. |
| R-CMP-06 | Les **tests** comparent toujours les groupes de l'axe, toutes couleurs confondues. Une note le dit, avec la disposition choisie et les valeurs regroupées. |

## Données et API

- `GET /datasets/{id}/compare` accepte `numbers` (colonnes à garder en nombres, séparées par des virgules).
- La réponse porte `categories` : les colonnes lues comme catégories par R-CMP-01, chacune avec son nombre de valeurs.
- `Group` porte `color` : la modalité de couleur de la boîte, ou null sans couleur.
- La réponse porte `layout` : la colonne sur l'axe, la colonne en couleur, `swapped`, le nombre de valeurs de chacune et le nombre gardé, et une phrase qui explique la disposition.

## Critères d'acceptation

- GIVEN Titanic WHEN X = Pclass, Y = Age THEN le visuel est en groupes (boîtes), avec 3 groupes « 1 », « 2 », « 3 » dans cet ordre, une ANOVA, et `categories` contient Pclass.
- GIVEN `numbers=Pclass` THEN le visuel redevient un nuage de points.
- GIVEN X = Survived, Y = Age, couleur = Sex THEN il y a 4 groupes (False et True, chacun pour female et male), chacun avec son effectif et ses quartiles, et une boîte par couleur sur le graphique.
- GIVEN Survived × Age, couleur = Embarked (3) THEN pas d'échange : 2 × 3 = 6 boîtes.
- GIVEN Sex × Age, couleur = SibSp (7 valeurs, lu comme catégorie) THEN SibSp passe sur l'axe, Sex en couleur (`swapped`), et 7 × 2 = 14 boîtes.
- GIVEN deux catégories de 10 et 7 valeurs THEN 3 groupes × 5 couleurs = 15 boîtes, « Others » compris, et `layout` le dit.
- GIVEN X = Age, Y = Sex, couleur = Pclass THEN on obtient la même disposition que pour X = Sex, Y = Age, couleur = Pclass.
- GIVEN Pclass (3 valeurs) × Survived (2 valeurs) THEN le visuel est un tableau croisé (deux catégories).
- GIVEN un nombre discret de 50 valeurs THEN il reste un nombre.
