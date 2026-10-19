# 023 — Module Données synthétiques

## Objectif

Générer un **jeu de données artificiel** qui ressemble au dataset d'origine (mêmes distributions, mêmes liens entre colonnes) sans en recopier les lignes. Le module dit ensuite clairement **à quel point il est fidèle** et **à quel point il protège les lignes réelles**. Le résultat peut devenir un nouveau dataset, explorable dans toutes les pages.

Usages : partager des données sans exposer les vraies lignes, créer un jeu de démonstration, tester une analyse.

Origine : [modules-futurs/donnees-synthetiques.md](../../modules-futurs/donnees-synthetiques.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md).

**Périmètre de la 023 : sans nouvelle dépendance** (choix du 2026-10-19). Les méthodes s'appuient sur numpy, scipy et scikit-learn, déjà installés.

**023b (plus tard, avec accord sur PyTorch)** : CTGAN et TVAE (paquet `ctgan`, licence MIT), TimeGAN (codé dans le projet). SDV est écarté : sa licence (Business Source License) n'est pas open source.

**Références de l'évaluation** : SDMetrics (MIT), table-evaluator (MIT) et Sweetviz (MIT), étudiés dans [la note de recherche](../../research/evaluation-donnees-synthetiques.md). Leurs formules sont **réimplémentées** (numpy, scipy, scikit-learn) ; aucun de ces paquets n'est ajouté.

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
3. En tête, quatre chiffres avec leur verdict : **Diagnostic** (données valides), **Quality** (ressemblance, calculée comme SDMetrics), **Detection** (un classifieur ne les distingue pas), **Privacy** (pas de copie ni de mémorisation).
4. Je parcours les colonnes **de la plus abîmée à la moins abîmée**, réel et synthétique côte à côte (en %, mêmes intervalles, statistiques appariées avec leur écart), puis les liens entre colonnes (réel, synthétique, écart).
5. Je choisis une cible pour voir si le synthétique garde son **pouvoir prédictif** (entraîné sur synthétique vs sur réel, testés sur les mêmes vraies lignes) et si le lien avec la cible est conservé colonne par colonne.
6. Je vois le **bilan de confidentialité** : copies exactes, protection contre la mémorisation, valeurs rares reproduites, et en option le risque de deviner une colonne sensible.
7. Je compare plusieurs générations (méthodes ou réglages différents) côte à côte.
8. Je clique **Save as dataset** : un nouveau dataset « sales (synthetic) » apparaît, avec les mêmes types de colonnes, ouvert dans Overview.

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
- **Arbres CART** : au moins 5 lignes réelles par feuille (une feuille ne désigne jamais une seule ligne réelle, contrainte de confidentialité). « Smooth numbers » (**activé par défaut**) : un bruit gaussien proportionnel à la dispersion de la feuille est ajouté aux nombres continus ayant au moins 20 valeurs distinctes (ni entiers, ni dates : leurs valeurs nouvelles trahiraient le synthétique).
- **« Drop copies of real rows »** (activé par défaut, toutes méthodes) : les lignes synthétiques identiques à une ligne d'apprentissage sont remplacées par des lignes générées en plus (règle « replicated uniques » de synthpop) ; leur nombre est affiché avec le run.
- **Lignes d'apprentissage** : 80 % des lignes réelles, au plus 50 000 (échantillon reproductible, graine affichée). Les 20 % restants sont **tenus à l'écart** pour l'évaluation de confidentialité.
- **Nombre de lignes générées** : par défaut autant que l'original, de 100 à 1 000 000.
- **Graine** : fixe par défaut (42), modifiable. La même graine avec les mêmes réglages redonne le même jeu.

## 3. Le rapport : vue d'ensemble

Le rapport suit la structure de SDMetrics, que les spécialistes connaissent :
- des **propriétés** notées de 0 à 100 % ;
- chaque propriété est la moyenne de ses détails (par colonne ou par paire) ;
- chaque détail est consultable.

L'évaluation porte sur un échantillon reproductible de 20 000 lignes d'apprentissage et 20 000 lignes synthétiques au plus. Les lignes réelles **tenues à l'écart** (20 %, section 2) servent à l'utilité et à la confidentialité.

En tête de page, quatre chiffres, chacun avec un verdict en une phrase :

| Chiffre | Ce qu'il dit | Bon si |
|---|---|---|
| **Diagnostic** | Les données sont valides : bornes, catégories, identifiants, structure | 100 % (sinon c'est un défaut du générateur, signalé) |
| **Quality** | Les données ressemblent au réel : formes des colonnes et liens entre colonnes | ≥ 85 % « Very close », ≥ 70 % « Close », ≥ 50 % « Rough », sinon « Far from the real data » |
| **Detection** | Un classifieur ne sait pas distinguer réel et synthétique | proche de 100 % |
| **Privacy** | Aucune ligne copiée, pas de mémorisation | voir section 6 |

**Le score Quality est calculé exactement comme celui de SDMetrics** : moyenne de Column shapes et de Column pair trends. Il est donc comparable aux scores publiés. Les autres mesures (couverture, vides, détection, utilité) sont affichées à côté, sans être fondues dans un score unique. Un score fourre-tout qui moyenne des échelles différentes est le défaut relevé chez table-evaluator.

## 4. Diagnostic et qualité

**Diagnostic** (contrôles de validité, attendu 100 %, un détail par colonne) :

| Contrôle | Colonnes | Calcul |
|---|---|---|
| Boundary adherence | numériques, dates | part des valeurs synthétiques dans [min, max] du réel (ou des bornes choisies) |
| Category adherence | catégories, booléens, ordinaux | part des valeurs synthétiques qui existent dans le réel |
| Key uniqueness | identifiants régénérés, colonnes « Keep unique » | 1 − part de doublons |
| Table structure | toutes | colonnes du synthétique = colonnes modélisées, avec le même type |
| Integer adherence | entiers | part des valeurs entières (contrôle propre à l'app) |

Par construction, les méthodes de la 023 doivent toujours obtenir 100 %. Le diagnostic sert de filet de sécurité, et il deviendra utile avec CTGAN et TVAE (023b), qui peuvent sortir des bornes.

**Quality, propriété Column shapes** (une note par colonne) :
- numériques et dates : **KSComplement** = 1 − statistique de Kolmogorov–Smirnov (dates converties en nombres, valeurs vides ignorées) ;
- catégories, booléens, ordinaux : **TVComplement** = 1 − ½ Σ |part réelle − part synthétique|.

**Quality, propriété Column pair trends** (une note par paire) :
- deux colonnes numériques ou dates : **CorrelationSimilarity** = 1 − |r_synthétique − r_réel| / 2 (Pearson ; Spearman en option) ;
- deux colonnes catégorielles : **ContingencySimilarity** = 1 − ½ ΣΣ |part réelle − part synthétique| sur le tableau croisé normalisé, la valeur vide comptant comme une modalité ;
- paire mixte : la colonne continue est découpée en 10 intervalles égaux **calculés sur le réel**, appliqués aux deux jeux, puis ContingencySimilarity.
- **Seules les paires où le réel montre un vrai lien comptent dans la moyenne** : |r| > 0,5, ou V de Cramér > 0,3 pour les paires catégorielles et mixtes, comme SDMetrics depuis la 0.27. Le détail liste toutes les paires avec une colonne « Meets threshold ». Sans aucune paire retenue, la propriété dit « No strong link in the real data to keep ».

**À côté du score (couverture et vides)**, une note par colonne :
- **Range coverage** = 1 − (part de l'étendue réelle manquée en bas + en haut) ;
- **Category coverage** = part des modalités réelles présentes dans le synthétique ;
- **Missing values** = 1 − |taux de vides réel − synthétique| ;
- **Outlier coverage** = min(1, part synthétique / part réelle des valeurs hors des clôtures 1,5 × IQR du réel).

Une faible couverture signale un générateur qui « s'effondre » sur les valeurs les plus fréquentes.

**Écarté** : le test du khi-deux (CSTest, déconseillé par SDMetrics), les vraisemblances BN, GM et LSTM, le score « basic statistics » de table-evaluator.

## 5. Détection et utilité

**Detection** (« real or synthetic? »), présentée comme une mesure de **fidélité**, pas de confidentialité :
- réel et synthétique (même nombre de lignes, 10 000 au plus de chaque côté) sont empilés et étiquetés ;
- deux détecteurs, chacun en validation croisée stratifiée 3 plis :
  - régression logistique (après imputation et mise à l'échelle robuste), comme SDMetrics, donc comparable ;
  - **HistGradientBoosting**, un détecteur plus fort qui voit les interactions ;
- score = 1 − (max(AUC, 0,5) × 2 − 1) : 100 % = indiscernables ; on garde le **plus sévère** des deux ;
- **What gives it away** : les colonnes que le détecteur fort utilise le plus (importance par permutation), avec un lien vers leur comparaison détaillée.

**Utility** (option : je choisis une colonne cible) :
- deux modèles identiques (HistGradientBoosting) :
  - **TRTR** : entraîné sur les lignes réelles d'apprentissage ;
  - **TSTR** : entraîné sur le synthétique ;
- **les deux sont testés sur les mêmes lignes réelles tenues à l'écart**. C'est la correction des défauts de table-evaluator (test sur du synthétique, pas de lignes tenues à l'écart) et de SDMetrics (pas de référence TRTR) ;
- métriques : R² et MAE pour une régression ; exactitude équilibrée, F1 macro et AUC pour une classification ;
- résultat : les deux scores côte à côte et leur rapport, par exemple « The synthetic data keeps 92 % of the real data's predictive power ».

## 6. Confidentialité

Calculée avec les lignes réelles **tenues à l'écart** (jamais vues par le générateur) comme référence.

**Distance entre deux lignes** (définition de SDMetrics) :
- nombre ou date : |a − b| / étendue réelle, plafonnée à 1 ;
- catégorie ou valeur vide : 0 si identiques, 1 sinon ;
- distance de la ligne = moyenne sur les colonnes modélisées.

**DCR** (distance to closest record) d'une ligne : la distance à la ligne la plus proche d'un jeu de référence. Calcul par blocs, sur 5 000 lignes synthétiques au plus.

**Mesures :**

| Mesure | Calcul | Lecture |
|---|---|---|
| **Exact copies** | part des lignes synthétiques strictement égales à une ligne d'apprentissage | attendu 0 % ; sinon avertissement avec le nombre de lignes |
| **Near copies** (New row synthesis de SDMetrics) | part des lignes égales à une ligne d'apprentissage, nombres à 1 % de l'étendue près | informatif : naturellement plus élevé avec peu de colonnes |
| **Overfitting protection** | min(1, 2 × (1 − part des lignes synthétiques plus proches de l'apprentissage que des lignes tenues à l'écart)) | 100 % = le générateur n'a pas mémorisé ; sous 80 %, avertissement « memorisation » |
| **Baseline protection** | min(1, médiane DCR(synthétique → apprentissage) / médiane DCR(données aléatoires uniformes dans les étendues → apprentissage)) | proche de 100 % = les lignes synthétiques ne sont pas plus proches du réel que du hasard. Un score bas n'est pas un défaut en soi (des données fidèles sont proches du réel) ; il se lit avec l'Overfitting protection |
| **Rare values** | modalités rares (< 5 lignes réelles) reproduites dans le synthétique | liste ; une valeur rare peut identifier une personne |
| **Disclosure protection (CAP)**, option | je choisis des colonnes « connues » (ex. âge, code postal) et une colonne « sensible » (ex. revenu). Pour chaque ligne réelle, les lignes synthétiques ayant les mêmes valeurs connues votent pour la valeur sensible ; protection = part de votes faux, rapportée à une référence aléatoire, plafonnée à 1. Variantes : zero-CAP et generalized-CAP | 100 % = connaître les colonnes connues n'aide pas à deviner la colonne sensible |

- **Graphique** : distributions des DCR superposées, synthétique → apprentissage et tenu à l'écart → apprentissage.
- **Verdict** : « No copied rows, and synthetic rows are no closer to the real ones than new real rows would be » ou l'avertissement correspondant.
- Une ligne rappelle que le synthétique **n'est pas** une garantie de confidentialité différentielle.
- **Écarté** : les attaques par modèle (beta chez SDMetrics), la « membership inference » et le k-anonymat de table-evaluator (mal construits).

## 7. Comparaison réel / synthétique (colonne par colonne)

Inspirée de Sweetviz, mais avec des mesures d'écart, ce qui manque à Sweetviz.

**Règles communes :**
- **une couleur fixe par jeu** dans tous les graphiques et nombres (réel : gris foncé ; synthétique : couleur d'accent, avec contour pour ne pas dépendre de la couleur) ;
- **tout comptage est aussi donné en % de son propre jeu**, car les deux jeux n'ont pas forcément la même taille.

**En-tête :**
- lignes réelles et synthétiques, lignes dupliquées dans chaque jeu ;
- colonnes par type ;
- colonnes laissées de côté, avec leur raison.

**Liste des colonnes :**
- une ligne compacte par colonne : nom, type, score (KS ou TV), mini-graphique superposé, et la plus grosse différence en clair (par exemple « mean +4 % », « 'Lyon' 12 % → 18 % ») ;
- **triée par défaut de la colonne la plus abîmée à la moins abîmée** ;
- un clic déplie le détail.

**Détail d'une colonne numérique ou date :**
- **bande de base** : valeurs, vides, distinctes, zéros, en comptage et en % pour chaque jeu ;
- **histogrammes superposés sur les mêmes intervalles** (calculés sur le réel), en % de chaque jeu ; boutons Auto · 10 · 30 intervalles ; bascule **ECDF** (fonctions de répartition superposées, lisibles pour voir des queues coupées) ;
- **statistiques appariées** : libellé, réel, synthétique, **Δ** (absolu et en %), sur min, 5 %, Q1, médiane, Q3, 95 %, max, moyenne, écart-type, IQR, asymétrie, aplatissement ;
- **valeurs les plus fréquentes, plus petites et plus grandes** (10 chacune), avec leur fréquence dans l'autre jeu. Elles repèrent la mémorisation, les queues coupées et les arrondis.

**Détail d'une colonne catégorielle :**
- même bande de base ;
- **tableau aligné** : modalité, réel %, synthétique %, Δ, sur l'union des modalités (0 % si absente d'un côté, marquée « missing in synthetic » ou « invented »), trié par fréquence réelle ; au-delà de 20, le reste en « Others » ;
- barres horizontales appariées.

**Cible superposée** (option, je choisis une cible) :
- par intervalle ou par modalité, la moyenne de la cible (ou la part de « vrai ») dans le réel et dans le synthétique, en deux lignes ;
- elle montre si le **lien avec la cible** est conservé, pas seulement les distributions.

**Liens entre colonnes :**
- trois matrices : réel, synthétique et **|écart|** (séquentielle, plafonnée à 0,3 comme table-evaluator) ;
- mesures du module Correlations : Pearson ou Spearman, V de Cramér, η ;
- un clic sur une case ouvre la paire : nuage de points réel et synthétique côte à côte (deux nombres), boîtes à moustaches par modalité (mixte), tableaux croisés en % (deux catégories) ;
- **les 5 paires les plus abîmées** sont listées.

**Vues d'ensemble** (onglet Overview) :
- **nuage moyenne / écart-type** : un point par colonne numérique, réel en x, synthétique en y, échelles log, diagonale ; les colonnes loin de la diagonale sont nommées ;
- **PCA** : 2 composantes ajustées sur le réel, réel et synthétique projetés et superposés.

**Comparaison de runs :**
- cochez 2 à 5 runs du même dataset ;
- tableau côte à côte : Diagnostic, Quality (et ses propriétés), Detection, Privacy, Utility si calculée, durée ;
- le meilleur score de chaque ligne est marqué ; un graphique en barres groupées montre les propriétés par méthode.

## 8. Résultat et nouveau dataset

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
- **Fichiers** : `datasets/<id>/synthetic/<run>/` : `data.parquet` (données), `train.parquet` et `holdout.parquet` (lignes réelles typées, pour les évaluations à la demande), `report.json` (rapport) ; supprimés avec le dataset source. Le dataset créé reste indépendant.
- **Endpoints** :
  - `GET /modules/synthetic/datasets/{id}/plan` : traitement automatique de chaque colonne, avec règle et raison, et méthode recommandée ;
  - `POST /modules/synthetic/datasets/{id}/runs` : lance la génération (job) ;
  - `GET /modules/synthetic/jobs/{job}` : progression et étape ;
  - `DELETE /modules/synthetic/jobs/{job}` : annulation ;
  - `GET /modules/synthetic/datasets/{id}/runs[/{run}]` : liste des runs et rapport complet ;
  - `GET …/runs/{run}/preview` : aperçu ;
  - `GET …/runs/{run}/download?format=csv|parquet` : téléchargement ;
  - `POST …/runs/{run}/dataset` : crée le dataset ;
  - `POST …/runs/{run}/utility` : évaluation d'utilité (TSTR / TRTR), avec la cible en paramètre ;
  - `POST …/runs/{run}/disclosure` : risque de divulgation (CAP), avec les colonnes connues et la colonne sensible ;
  - `GET …/runs/{run}/columns/{column}` : comparaison détaillée d'une colonne (section 7), avec la cible en option ;
  - `GET …/runs/{run}/pairs?a=&b=` : une paire réelle et synthétique côte à côte (section 7, liens) ;
  - `GET …/runs/compare?runs=a,b,c` : scores côte à côte de plusieurs runs ;
  - `GET /modules/synthetic/origin/{dataset}` : source et run d'un dataset créé depuis des données synthétiques ;
  - `GET /settings/gpu?refresh=` : carte graphique détectée ;
  - `DELETE …/runs/{run}`.
- **Code** (forme compatible avec la future bibliothèque Python : calculs purs, entrées simples, dataclasses en sortie) :
  - `backend/app/domain/synthetic/` : `plan.py` (règles R-SYN), `encode.py` (aller-retour colonnes ↔ matrice), `methods/` (cart, copula, bayes, independent), `diagnostic.py`, `quality.py` (formes, paires, couverture), `detection.py`, `utility.py`, `privacy.py` (copies, DCR, CAP), `compare.py` (vue colonne par colonne) ;
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

**Diagnostic :**
- GIVEN une génération de chacune des 4 méthodes THEN le Diagnostic vaut 100 % (bornes, catégories, identifiants uniques, structure, entiers).
- GIVEN un jeu synthétique trafiqué (une valeur hors bornes, une catégorie inventée, un identifiant en double) THEN chaque contrôle concerné tombe sous 100 % et nomme la colonne.

**Qualité (formules vérifiées) :**
- GIVEN des jeux construits à la main THEN KSComplement, TVComplement, CorrelationSimilarity, ContingencySimilarity, RangeCoverage, CategoryCoverage et MissingValueSimilarity donnent les valeurs calculées à la main (tests unitaires par formule, mêmes définitions que SDMetrics).
- GIVEN une paire réelle sans lien (|r| < 0,5, V < 0,3) THEN elle apparaît dans le détail avec « Meets threshold: no » et ne compte pas dans le score Column pair trends.
- GIVEN deux colonnes très liées (corrélation 0,9) THEN CART et la copule gardent la corrélation à ± 0,1, la méthode indépendante la perd, et le score Column pair trends les classe dans cet ordre.

**Détection et utilité :**
- GIVEN le synthétique = une copie des lignes d'apprentissage THEN le score de détection est proche de 100 % (indiscernable) et la confidentialité signale 100 % de copies : les deux mesures se répondent.
- GIVEN une cible WHEN je lance l'utilité THEN les deux modèles (TSTR, TRTR) sont testés sur les mêmes lignes réelles tenues à l'écart, et le rapport s'affiche.

**Confidentialité :**
- GIVEN un synthétique sain THEN 0 copie exacte, Overfitting protection ≥ 0,9, Baseline protection proche de 1.
- GIVEN un synthétique fabriqué en bruitant à peine les lignes d'apprentissage THEN Overfitting protection chute et l'avertissement de mémorisation apparaît.
- GIVEN des colonnes connues et une colonne sensible WHEN je lance le CAP THEN le score est comparé à la référence aléatoire.

**Comparaison :**
- GIVEN réel et synthétique de tailles différentes THEN tous les comptages sont aussi donnés en % de leur jeu, et les histogrammes partagent les mêmes intervalles.

**Résultat :**
- GIVEN un run WHEN je clique Save as dataset THEN un dataset prêt apparaît avec les mêmes types de colonnes que la source et la mention de son origine.

**Transverse :**
- **Annulation** : le job s'arrête entre deux étapes et n'enregistre rien.
- **Accessibilité** : scores et verdicts en texte, graphiques avec légende, réel et synthétique différenciés autrement que par la couleur (gris plein / accent avec contour).

## GPU (préparé pour la 023b)

Les modèles profonds de la 023b (CTGAN, TVAE, TimeGAN) s'entraînent beaucoup plus vite sur une carte graphique. L'app **détecte** la carte et laisse l'utilisateur **choisir**.

**Détection, au démarrage puis à la demande (« Check again ») :**
- Sans PyTorch : présence de `nvidia-smi`, nom de la carte, mémoire, version du pilote.
- Avec PyTorch : `torch.cuda.is_available()`, puis la version CUDA de PyTorch, compatible ou non avec le pilote. Apple Silicon : `torch.backends.mps.is_available()`.
- Résultat, un état parmi :
  - « NVIDIA GeForce RTX 4050 Laptop · 6 GB · ready » ;
  - « GPU found but this build has no GPU support (CPU PyTorch) » ;
  - « No GPU found ».
- Dans Docker, l'image par défaut est sans GPU : l'état le dit et renvoie au guide pour l'image « full » avec `--gpus all`.

**Choix de l'utilisateur :**
- **Settings › Compute** :
  - « Use the GPU when available » (On / Off, défaut : On si une carte prête est détectée) ;
  - l'état détecté, avec la carte, la mémoire et « Check again ».
  - Le réglage est enregistré dans la table `settings` et vaut pour toute l'app.
- **Sur la page Synthetic data**, au lancement d'un modèle profond : une pastille « GPU · RTX 4050 » ou « CPU » à côté de Generate, avec un interrupteur pour ce run seulement. Désactivé avec sa raison si aucune carte n'est prête.
- **Repli automatique sur le CPU** si la carte manque de mémoire en cours d'entraînement (CUDA out of memory). Le run continue sur le CPU et le dit (« GPU ran out of memory: finished on CPU »).
- **Chaque run enregistre** l'appareil utilisé (CPU, ou nom de la carte) et la durée, pour comparer.

**Au-delà du module :** le même réglage servira au module Machine learning pour XGBoost (`device="cuda"`) et LightGBM quand leur version GPU est installée.

**En 023 (sans PyTorch) :**
- L'état de détection est déjà affiché dans Settings › Compute, à partir de `nvidia-smi`.
- Le réglage existe mais reste sans effet, avec la mention « Used by the deep models (CTGAN, TVAE, TimeGAN), coming next ».
- Les méthodes de la 023 tournent sur le CPU : elles n'ont pas besoin d'un GPU.

## Hors scope (023)

- CTGAN, TVAE, TimeGAN, modèles de diffusion (023b, avec PyTorch).
- Confidentialité différentielle.
- Génération conditionnelle (« seulement des clients français »).
- Données multi-tables.
