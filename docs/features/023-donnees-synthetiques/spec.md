# 023 — Module Données synthétiques

## Objectif

Générer un **jeu de données artificiel** qui ressemble au dataset d'origine (mêmes distributions, mêmes liens entre colonnes) sans en recopier les lignes. Le module dit ensuite clairement **à quel point il est fidèle** et **à quel point il protège les lignes réelles**. Le résultat peut devenir un nouveau dataset, explorable dans toutes les pages.

Usages : partager des données sans exposer les vraies lignes, créer un jeu de démonstration, tester une analyse.

Origine : [modules-futurs/donnees-synthetiques.md](../../modules-futurs/donnees-synthetiques.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md).

**Périmètre de la 023 : sans nouvelle dépendance** (choix du 2026-10-19). Les méthodes s'appuient sur numpy, scipy et scikit-learn, déjà installés.

**023b (plus tard, avec accord sur PyTorch)** : CTGAN et TVAE (paquet `ctgan`, licence MIT), TimeGAN (codé dans le projet). SDV est écarté : sa licence (Business Source License) n'est pas open source.

## Principe : automatique d'abord, comme le reste de l'app

- La page s'ouvre **prête à générer** : toutes les colonnes utilisables, la méthode recommandée, autant de lignes que l'original. Un seul clic : **Generate**.
- Chaque choix automatique est affiché avec sa raison, par exemple :
  - « CART: best fidelity on mixed columns » ;
  - « customer_id: new identifiers in the same format » ;
  - « comment: left out, free text could leak real content ».
- Tout se change ensuite : colonnes, méthode, nombre de lignes, contraintes.

## User stories

1. J'ouvre **Synthetic data**. Les colonnes sont listées avec ce que l'app va en faire. Je clique **Generate**.
2. Une barre de progression suit les étapes : apprentissage, génération, évaluation. Je peux annuler.
3. Je vois un **score de fidélité** global et une phrase de verdict, puis le détail :
   - colonne par colonne, avec la distribution réelle et la distribution synthétique superposées ;
   - les liens entre colonnes ;
   - le test « réel ou synthétique ? ».
4. Je vois un **bilan de confidentialité** : aucune ligne copiée, distance au plus proche enregistrement réel, catégories rares reproduites.
5. Je compare plusieurs générations (méthodes ou réglages différents) dans une liste de runs.
6. Je clique **Save as dataset** : un nouveau dataset « sales (synthetic) » apparaît, avec les mêmes types de colonnes, ouvert dans Overview.

## 1. Préparation automatique des colonnes

Chaque colonne reçoit un **traitement**, choisi par une règle identifiée (raison affichée, modifiable sauf contrainte) :

| Id | Colonne | Traitement par défaut |
|---|---|---|
| R-SYN-01 | numérique continue | modélisée ; bornes min/max réelles respectées ; nombre de décimales conservé |
| R-SYN-02 | numérique discrète (entiers) | modélisée, arrondie à l'entier |
| R-SYN-03 | catégorielle, booléenne, ordinale | modélisée ; seules des modalités existantes sont produites |
| R-SYN-04 | date / date-heure | modélisée comme un nombre (secondes), reconvertie, arrondie au jour s'il n'y a jamais d'heure |
| R-SYN-05 | identifiant | **régénéré** : nouvelles valeurs uniques au même format (« C00001 » → « C08412 ») ; jamais une valeur réelle |
| R-SYN-06 | texte libre, e-mail, téléphone, URL | **laissé de côté** (il pourrait recopier un contenu réel) ; peut être réintégré en tirant des valeurs « fictives » au même format (option) |
| R-SYN-07 | colonne exclue dans Columns, ou plus de 95 % de valeurs vides | laissée de côté |
| R-SYN-08 | catégorielle de plus de 200 modalités | modalités rares (< 5 lignes) regroupées en « Other » avant l'apprentissage, pour ne pas reproduire des valeurs quasi uniques (contrainte de confidentialité) |

- **Valeurs vides** : le taux de vides de chaque colonne est appris (un état « vide » par colonne) et reproduit.
- **Choix possibles par colonne** : Model · Keep unique (nouvelles valeurs uniques) · Leave out.
- **Contraintes** : bornes personnalisées (min / max), colonnes à garder uniques.

## 2. Méthodes

| Méthode | Principe | Quand |
|---|---|---|
| **Sequential CART** ★ (défaut) | À la manière de synthpop. Les colonnes sont générées l'une après l'autre. Chacune est prédite par un arbre de décision appris sur les colonnes déjà générées ; pour chaque ligne synthétique, on tire une **valeur réelle de la même feuille**. | Le meilleur compromis sur des données mixtes ; capture les liens non linéaires et les interactions |
| Gaussian copula | Chaque colonne est ramenée à une loi normale (via ses quantiles ou ses fréquences). Une matrice de corrélation est apprise, puis on tire et on revient aux échelles d'origine. | Rapide ; liens monotones ; bonne base de comparaison |
| Bayesian network | Les colonnes sont discrétisées, puis reliées par un arbre de Chow-Liu (dépendances les plus fortes, information mutuelle) ; on tire chaque colonne sachant sa colonne parente. Les numériques sont tirées dans leur intervalle selon la distribution réelle. | Données surtout catégorielles ; structure lisible (l'arbre est montré) |
| Independent columns | Chaque colonne est tirée seule selon sa distribution | **Référence** : montre ce qu'on perd sans les liens ; jamais recommandée |

**Règles :**
- **Ordre des colonnes pour CART (Auto)** : d'abord la colonne la plus liée aux autres (somme des associations du module Correlations), puis par lien décroissant avec les colonnes déjà placées. La première colonne est tirée selon sa distribution réelle.
- **Arbres CART** : au moins 5 lignes réelles par feuille (une feuille ne désigne jamais une seule ligne réelle, contrainte de confidentialité). Option « Smooth numbers » : un bruit gaussien proportionnel à la dispersion de la feuille est ajouté aux nombres.
- **Lignes d'apprentissage** : 80 % des lignes réelles, au plus 50 000 (échantillon reproductible, graine affichée). Les 20 % restants sont **tenus à l'écart** pour l'évaluation de confidentialité.
- **Nombre de lignes générées** : par défaut autant que l'original, de 100 à 1 000 000.
- **Graine** : fixe par défaut (42), modifiable. La même graine avec les mêmes réglages redonne le même jeu.

## 3. Évaluation de la fidélité

Calculée sur un échantillon de 20 000 lignes réelles (lignes d'apprentissage) et 20 000 lignes synthétiques au plus.

| Mesure | Calcul | Score (0–100 %) |
|---|---|---|
| **Column shapes** | numériques et dates : statistique de Kolmogorov–Smirnov ; catégories : distance de variation totale ; plus l'écart du taux de vides | 1 − écart, moyenne sur les colonnes |
| **Column pairs** | matrice d'associations réelle et synthétique (Pearson entre nombres, V de Cramér entre catégories, rapport de corrélation η en mixte, comme Correlations) ; écart absolu moyen | 1 − écart moyen |
| **Real or synthetic?** | un classifieur (HistGradientBoosting, validation croisée 5 plis) apprend à distinguer les lignes réelles des synthétiques ; AUC | 1 − 2 × \|AUC − 0,5\| (100 % = indiscernables) |

- **Score global** = moyenne des trois scores, avec un verdict en une phrase :
  - ≥ 85 % : « Very close to the real data » ;
  - ≥ 70 % : « Close: most patterns are kept » ;
  - ≥ 50 % : « Rough: shapes are kept, some links are lost » ;
  - en dessous : « Far from the real data ».
- **Détail par colonne** : score, distributions superposées (histogrammes ou barres, réel en gris, synthétique dans la couleur d'accent), moyenne et écart-type ou part des modalités principales, réel vs synthétique.
- **Détail des liens** : deux matrices côte à côte (réel, synthétique) et la matrice des écarts (divergente, gris à 0) ; les 5 paires les plus abîmées sont listées.
- **Ce qui trahit le synthétique** : les colonnes que le classifieur utilise le plus (importance par permutation) pour reconnaître une ligne synthétique.
- **Utilité (option)** : « Train on synthetic, test on real ». Je choisis une colonne cible ; un modèle est entraîné sur le synthétique puis testé sur les lignes réelles tenues à l'écart, et comparé au même modèle entraîné sur les lignes réelles. Résultat affiché comme le rapport des deux scores (R² ou exactitude équilibrée).

## 4. Confidentialité

Calculée avec les lignes réelles **tenues à l'écart** (jamais vues par le modèle) comme référence. Distances de Gower : numériques normalisées par leur étendue, catégories 0/1.

- **Exact copies** : lignes synthétiques identiques à une ligne d'apprentissage, sur toutes les colonnes modélisées. Attendu : 0. Au-delà, avertissement nommant le nombre.
- **Distance to closest record (DCR)** : pour chaque ligne synthétique, la distance à la ligne d'apprentissage la plus proche, comparée à la même distance calculée pour les lignes tenues à l'écart.
  - Si les lignes synthétiques sont nettement plus proches des lignes d'apprentissage que ne le sont des lignes réelles jamais vues (médiane DCR synthétique < 0,8 × médiane DCR tenue à l'écart), le modèle **a mémorisé** : avertissement.
  - Graphique : les deux distributions de DCR superposées.
- **Rare values** : modalités rares (< 5 lignes réelles) présentes dans le synthétique, listées.
- **Verdict** : « No copied rows, synthetic rows are no closer to the real ones than new real rows would be » ou l'avertissement correspondant.
- Le synthétique **n'est pas** une garantie de confidentialité différentielle ; la page le dit en une ligne.

## 5. Résultat et nouveau dataset

- **Aperçu** : les 100 premières lignes synthétiques.
- **Save as dataset** :
  - le jeu complet est écrit en Parquet, puis importé par l'import habituel ;
  - **les types, rôles, ordres et parseurs des colonnes sont recopiés** depuis la source (pas de nouvelle détection) ;
  - le dataset s'appelle « <source> (synthetic) » et s'ouvre dans Overview ;
  - son en-tête affiche « Synthetic, from <source> » avec un lien vers le run.
- **Download** : CSV ou Parquet sans créer de dataset.
- **Runs** : chaque génération est un run (méthode, réglages, scores, durée) ; la liste permet de rouvrir, comparer (scores côte à côte) et supprimer.

## Données et API

- **Table `synthetic_runs`** (migration 0009) : id, dataset source, méthode, réglages (JSON), lignes générées, scores (JSON), statut, erreur, durée, dataset créé (nullable), créé le.
- **Fichiers** : `datasets/<id>/synthetic/<run>.parquet` (données) et `<run>.json` (rapport) ; supprimés avec le dataset source. Le dataset créé reste indépendant.
- **Endpoints** :
  - `GET /modules/synthetic/datasets/{id}/plan` : traitement automatique de chaque colonne, avec règle et raison, et méthode recommandée ;
  - `POST /modules/synthetic/datasets/{id}/runs` : lance la génération (job) ;
  - `GET /modules/synthetic/jobs/{job}` : progression et étape ;
  - `DELETE /modules/synthetic/jobs/{job}` : annulation ;
  - `GET /modules/synthetic/datasets/{id}/runs[/{run}]` : liste des runs et rapport complet ;
  - `GET …/runs/{run}/preview` : aperçu ;
  - `GET …/runs/{run}/download?format=csv|parquet` : téléchargement ;
  - `POST …/runs/{run}/dataset` : crée le dataset ;
  - `POST …/runs/{run}/utility` : évaluation d'utilité, avec la cible en paramètre ;
  - `DELETE …/runs/{run}`.
- **Code** :
  - `backend/app/domain/synthetic/` : `plan.py` (règles R-SYN), `encode.py` (aller-retour colonnes ↔ matrice), `methods/` (cart, copula, bayes, independent), `fidelity.py`, `privacy.py` ;
  - `backend/app/modules/synthetic/` ;
  - frontend `modules/synthetic/`.

## Limites

- Au plus 100 colonnes modélisées (au-delà, les moins liées sont laissées de côté avec un message).
- Au plus 50 000 lignes d'apprentissage et 1 000 000 de lignes générées.
- Les relations entre lignes ne sont pas modélisées : ordre temporel, plusieurs lignes par client. TimeGAN (023b) traitera les séries.
- **Performance cible** : 50 000 lignes × 20 colonnes, CART, génération de 50 000 lignes et évaluation en moins de 60 s (test lent à part).

## Critères d'acceptation

**Plan et génération :**
- GIVEN le jeu `typing_traps` WHEN j'ouvre la page THEN chaque colonne a un traitement avec sa règle : `customer_id` régénéré, `comment` et `email` laissés de côté, `signup_date` modélisée comme date ; la méthode proposée est Sequential CART.
- GIVEN une génération CART THEN aucune valeur hors des bornes réelles, aucune modalité inventée, les entiers restent entiers, et le taux de vides de chaque colonne est à ± 3 points du réel.
- GIVEN un identifiant régénéré THEN toutes les valeurs sont uniques, au même format, et aucune n'existe dans la source.
- GIVEN la même graine et les mêmes réglages THEN le même jeu est produit.

**Fidélité :**
- GIVEN deux colonnes très liées (corrélation 0,9) THEN CART et la copule gardent la corrélation à ± 0,1, la méthode indépendante la perd, et le score « Column pairs » les classe dans cet ordre.
- GIVEN un synthétique qui recopie les données réelles THEN l'AUC « real or synthetic » est proche de 0,5 et la confidentialité signale 100 % de copies exactes (le test vérifie que les deux mesures se répondent).

**Confidentialité :**
- GIVEN un synthétique sain THEN 0 copie exacte et un rapport DCR synthétique / tenu à l'écart ≥ 0,8.
- GIVEN un synthétique fabriqué en bruitant à peine les lignes d'apprentissage THEN l'avertissement de mémorisation apparaît.

**Résultat :**
- GIVEN un run WHEN je clique Save as dataset THEN un dataset prêt apparaît avec les mêmes types de colonnes que la source et la mention de son origine.

**Transverse :**
- **Annulation** : le job s'arrête entre deux étapes et n'enregistre rien.
- **Accessibilité** : scores et verdicts en texte, graphiques avec légende, réel et synthétique différenciés autrement que par la couleur (gris plein / accent avec contour).

## Hors scope (023)

- CTGAN, TVAE, TimeGAN, modèles de diffusion (023b, avec PyTorch).
- Confidentialité différentielle.
- Génération conditionnelle (« seulement des clients français »).
- Données multi-tables.
