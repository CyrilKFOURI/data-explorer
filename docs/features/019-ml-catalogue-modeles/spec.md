# 019 — Machine learning : catalogue de modèles, réglages à trois niveaux, optimiseurs, validation

## Objectif

Donner accès à **tous les modèles classiques** du ML tabulaire, **rangés par familles**, avec pour chacun des réglages en **trois niveaux** — essentiels, avancés, expert (dont l'algorithme d'optimisation) — sans jamais perdre la simplicité de l'app : un défaut justifié partout, un libellé en langage courant, les combinaisons impossibles bloquées avec leur raison. Remplace et étend l'ancien jalon « XGBoost, Random forest ». Référence : [11-machine-learning.md](../../pages/11-machine-learning.md).

## Ce qui garde l'identité de l'app (et la distingue d'une console ML type cloud)

- **Le choix du modèle se fait par intention, pas par nom d'API** : chaque modèle a une phrase (« Many small trees, each correcting the previous ones ») et des badges utiles (*Fast*, *Interpretable*, *Handles missing values*, *Needs lots of data*).
- **On ne voit que ce qui sert** : 2 ou 3 réglages essentiels ; le reste existe mais se déplie.
- **Le nom technique reste accessible** (`max_depth` en petit, police mono) pour ceux qui le connaissent, jamais en premier.
- **Les défauts dépendent des données** et l'app dit pourquoi.
- **Pas de jargon d'infrastructure** (instances, endpoints, conteneurs) : tout tourne en local.

## Sélecteur de modèle

Dans la colonne Réglages, la ligne **Model [ Logistic regression ▾ ]** ouvre un menu large et cherchable :

```
┌ Search models…                                                        ┐
│ RECOMMENDED FOR THIS DATA                                             │
│   XGBoost              Many small trees correcting each other   Fast · Missing ok │
│   Logistic regression  A weighted sum of the features           Interpretable     │
│ LINEAR MODELS          ▸                                                          │
│ TREES                  ▸                                                          │
│ BAGGING ENSEMBLES      ▸   (Random forest, Extra trees, Bagging)                  │
│ BOOSTING ENSEMBLES     ▸                                                          │
│ …                                                                                 │
└───────────────────────────────────────────────────────────────────────┘
```

- Familles repliables ; la recherche porte sur le nom, la famille et la description.
- **Recommended for this data** : 2 ou 3 modèles choisis par règles (taille, nombre de variables, part de catégories, vides, déséquilibre).
- Un modèle incompatible avec le problème n'apparaît pas (une régression ne propose pas Naive Bayes) ; un modèle incompatible avec les données est grisé avec sa raison (« Multinomial NB needs non-negative inputs »).
- Les modèles lents pour la taille du dataset portent un badge *Slow on 200 000 rows* (ex. SVM à noyau, Gaussian process) et une estimation de durée.
- Les modèles qui demandent un paquet absent de l'installation sont listés avec « Not installed in this build » (voir Dépendances).

## Catalogue

R = régression, C = classification. Les tâches non cochées ne sont pas proposées.

| Famille | Modèle | R | C | Notes |
|---|---|---|---|---|
| **Linear models** | Linear regression (OLS) | ✓ | | Coefficients, IC, p-values (statsmodels) |
| | Ridge · Lasso · Elastic net | ✓ | | Régularisation L2 / L1 / mixte |
| | Huber · Quantile regression | ✓ | | Robustes aux valeurs extrêmes ; quantile = prédire la médiane ou un percentile |
| | Bayesian ridge · ARD | ✓ | | Incertitude des coefficients |
| | Poisson · Gamma · Tweedie (GLM) | ✓ | | Comptages, montants positifs |
| | Logistic regression | | ✓ | Binaire et multinomiale |
| | Ridge classifier · Perceptron · Passive-aggressive | | ✓ | |
| | SGD (regressor / classifier) | ✓ | ✓ | Descente de gradient stochastique, gros volumes |
| **Discriminant analysis** | LDA · QDA | | ✓ | |
| **Nearest neighbours** | k-NN · Radius neighbours | ✓ | ✓ | |
| **Support vector machines** | Linear SVM | ✓ | ✓ | |
| | Kernel SVM (RBF, polynomial, sigmoid) · Nu-SVM | ✓ | ✓ | Lent au-delà de ~20 000 lignes |
| **Naive Bayes** | Gaussian · Multinomial · Complement · Bernoulli · Categorical | | ✓ | |
| **Trees** | Decision tree · Extra tree | ✓ | ✓ | Arbre affichable |
| **Bagging ensembles** | Random forest · Extra trees · Bagging | ✓ | ✓ | |
| **Boosting ensembles** | XGBoost | ✓ | ✓ | Défaut recommandé dès ~5 000 lignes |
| | LightGBM · CatBoost | ✓ | ✓ | Selon installation |
| | Histogram gradient boosting · Gradient boosting · AdaBoost | ✓ | ✓ | scikit-learn |
| **Neural networks** | Multi-layer perceptron (MLP) | ✓ | ✓ | |
| **Kernel & probabilistic** | Kernel ridge · Gaussian process | ✓ | ✓ (GP) | Petits datasets |
| **Combinations** | Voting · Stacking | ✓ | ✓ | À partir de runs existants (021) |

Chaque modèle déclare son **profil** (drapeaux de [017](../017-ml-preparation-donnees/spec.md)), ses réglages, leurs bornes, leurs défauts (éventuellement calculés), et ses incompatibilités.

## Trois niveaux de réglages

| Niveau | Où | Contenu | Pour qui |
|---|---|---|---|
| **1 · Essentials** | Colonne Réglages, sous le modèle | 2 ou 3 réglages qui changent vraiment le résultat | Tout le monde |
| **2 · Advanced** | Tiroir **Settings** (bouton « All settings »), onglet **Model** | Tous les hyperparamètres courants, groupés (Structure · Regularization · Sampling · Class balance) | Utilisateur averti |
| **3 · Expert** | Même tiroir, interrupteur **Expert** en haut ; ajoute l'onglet **Optimizer** et des champs dans les autres onglets | Algorithme d'optimisation, pas d'apprentissage, tolérances, itérations, précision, parallélisme, graine | Data scientist |

### Tiroir « Settings »

Panneau latéral droit (~480 px) par-dessus les résultats (qui restent visibles, atténués) :

```
Settings — XGBoost                           Expert ○   Reset all   ✕
[ Model ] [ Optimizer · expert ] [ Preparation ] [ Validation ] [ Rows ]

STRUCTURE
  Number of trees        [ 1000 ]  early stopping finds the right number   n_estimators
  Tree depth             [ 6 ]     4 if fewer than 5 000 rows               max_depth
  Min. weight per leaf   [ 1 ]                                              min_child_weight
REGULARIZATION
  L2 penalty             [ 1 ]                                              reg_lambda
  …
```

- Chaque réglage : libellé courant, champ (curseur pour les bornes connues, échelle log si pertinent), justification du défaut, nom technique à droite ; un point + « Reset » s'il est modifié.
- Les essentiels sont aussi présents ici (même valeur, synchronisés).
- Les **dépendances entre réglages** sont gérées : un champ sans effet est masqué (Strength masqué si Regularization = None) ; une combinaison impossible est désactivée avec la raison (« L1 penalty needs the liblinear or saga solver »).
- Le tiroir se ferme avec Échap ; **Train** reste accessible en bas du tiroir.

## Réglages par modèle (extraits normatifs ; tous les modèles suivent ce schéma)

### XGBoost

| Niveau | Réglage | Paramètre | Défaut |
|---|---|---|---|
| Essentials | Number of trees | `n_estimators` | 1 000 + early stopping (50) |
| | Tree depth | `max_depth` | 6 ; 4 si < 5 000 lignes |
| | Learning rate | `learning_rate` | 0,1 ; 0,05 si > 100 000 lignes |
| Advanced | Row / column sampling | `subsample`, `colsample_bytree`, `colsample_bylevel` | 0,8 / 0,8 / 1 |
| | Min. weight per leaf · Min. gain to split | `min_child_weight`, `gamma` | 1 · 0 |
| | L2 / L1 penalty | `reg_lambda`, `reg_alpha` | 1 / 0 |
| | Class balance | `scale_pos_weight` | auto (017, R-IMB-02) |
| | Early stopping patience | `early_stopping_rounds` | 50 |
| | Monotonic constraints | `monotone_constraints` | aucune (par variable : ↑ ↓) |
| Expert · Optimizer | Booster | `booster` | `gbtree` · `dart` · `gblinear` |
| | Tree construction | `tree_method` | `hist` · `approx` · `exact` |
| | Objective / loss | `objective` | selon le problème (squared error, absolute error, Huber, Poisson, Tweedie, logistic, softprob) |
| | Max bins · Max delta step | `max_bin`, `max_delta_step` | 256 · 0 |
| | Device · Threads | `device`, `n_jobs` | CPU (CUDA si détecté hors Docker) · tous les cœurs |

### Logistic regression

| Niveau | Réglage | Paramètre | Défaut |
|---|---|---|---|
| Essentials | Regularization strength | `C` | 1,0 (échelle log 1e-4 – 1e4) |
| | Balance classes | `class_weight` | auto (R-IMB-02) |
| Advanced | Penalty | `penalty` | L2 · L1 · Elastic net (+ `l1_ratio`) · none |
| | Decision threshold (binaire) | — | 0,5 · « best F1 » · « best balanced accuracy » (choisi sur la validation) |
| | Multiclass strategy | — | multinomial · one-vs-rest |
| Expert · Optimizer | Solver | `solver` | `lbfgs` (défaut) · `newton-cg` · `newton-cholesky` · `liblinear` · `sag` · `saga` |
| | Max iterations · Tolerance | `max_iter`, `tol` | 1 000 · 1e-4 |
| | Warm start · Intercept scaling | `warm_start`, `intercept_scaling` | non · 1 |

Compatibilités imposées : L1 → `liblinear` ou `saga` ; Elastic net → `saga` ; `newton-cholesky` → pas de multinomial avec beaucoup de classes ; `sag`/`saga` → variables à l'échelle (garanti par 017).

### Multi-layer perceptron (MLP)

| Niveau | Réglage | Paramètre | Défaut |
|---|---|---|---|
| Essentials | Hidden layers | `hidden_layer_sizes` | (64, 32) |
| | Regularization | `alpha` | 1e-4 |
| Advanced | Activation | `activation` | `relu` · `tanh` · `logistic` · `identity` |
| | Early stopping · Validation fraction | `early_stopping`, `validation_fraction` | oui · 0,1 |
| | Batch size | `batch_size` | `auto` (min(200, n)) |
| Expert · Optimizer | Optimizer | `solver` | **Adam** (défaut) · **SGD** · **L-BFGS** |
| | Learning rate (initial) · Schedule | `learning_rate_init`, `learning_rate` | 0,001 · `constant` · `invscaling` · `adaptive` (SGD) |
| | Momentum · Nesterov (SGD) | `momentum`, `nesterovs_momentum` | 0,9 · oui |
| | β1, β2, ε (Adam) | `beta_1`, `beta_2`, `epsilon` | 0,9 · 0,999 · 1e-8 |
| | Max epochs · Tolerance · Patience | `max_iter`, `tol`, `n_iter_no_change` | 200 · 1e-4 · 10 |

### SGD (descente de gradient stochastique)

| Niveau | Réglage | Paramètre | Défaut |
|---|---|---|---|
| Essentials | Loss | `loss` | R : squared error · Huber · epsilon-insensitive ; C : log loss · hinge · modified Huber |
| | Regularization | `penalty`, `alpha` | L2, 1e-4 |
| Expert · Optimizer | Learning-rate schedule | `learning_rate` | `optimal` · `constant` · `invscaling` · `adaptive` |
| | Initial rate · Power | `eta0`, `power_t` | 0,01 · 0,25 |
| | Averaging (ASGD) | `average` | non |
| | Epochs · Tolerance · Early stopping | `max_iter`, `tol`, `early_stopping` | 1 000 · 1e-3 · oui |

### Autres modèles (essentiels)

| Modèle | Essentiels | Optimiseur (expert) |
|---|---|---|
| Linear regression | Regularization (None · Ridge · Lasso · Elastic net), Strength | Méthode : moindres carrés exacts (QR) · descente de coordonnées (Lasso/EN) · `svd` · `cholesky` · `lsqr` · `sparse_cg` · `sag` · `saga` (Ridge) ; max_iter, tol |
| Random forest / Extra trees | Number of trees (300), Tree depth (∞), Min. rows per leaf (1 ; 5 si > 100 000) | Criterion (squared error, absolute error, Poisson / gini, entropy, log loss), bootstrap, max_samples, n_jobs |
| Decision tree | Tree depth (5), Min. rows per leaf (20) | Criterion, splitter (best · random), élagage `ccp_alpha` |
| LightGBM | Number of leaves (31), Learning rate (0,1), Number of trees (1 000 + early stopping) | Boosting (gbdt · dart · goss), min_data_in_leaf, feature_fraction, bagging, lambda_l1/l2 |
| CatBoost | Iterations (1 000 + early stopping), Depth (6), Learning rate (auto) | l2_leaf_reg, border_count, bootstrap type |
| Hist. gradient boosting | Max iterations (300 + early stopping), Learning rate (0,1), Max leaf nodes (31) | Loss, l2_regularization, max_bins |
| AdaBoost | Number of estimators (100), Learning rate (1,0) | Estimateur de base (arbre de profondeur 1–3) |
| k-NN | Neighbours k (√n borné 5–50, impair en binaire), Weights (uniform · distance) | Distance (Euclidean · Manhattan · Minkowski p · cosine), algorithme (auto · ball tree · KD tree · brute) |
| Kernel SVM | Kernel (RBF), C (1,0), γ (`scale`) | degree, coef0, tol, cache, shrinking ; probabilités (calibration) |
| Linear SVM | C (1,0) | Loss (hinge · squared hinge), dual, max_iter |
| Naive Bayes | Gaussian : var_smoothing · autres : α (1,0) | — |
| LDA / QDA | Solver (svd · lsqr · eigen), shrinkage (auto) / reg_param | — |
| Gaussian process | Kernel (RBF + bruit) | Optimiseur du noyau (L-BFGS-B), restarts |
| GLM Poisson/Gamma/Tweedie | α (1,0), power (Tweedie) | Solver (lbfgs · newton-cholesky), max_iter |

## Validation et lignes (onglets « Validation » et « Rows »)

| Réglage | Défaut | Options |
|---|---|---|
| Method | **80 / 20 split** (stratifié en classification) | k-fold CV (k = 3–10) · repeated k-fold · stratified group k-fold (si une colonne de groupe est choisie : jamais le même groupe en apprentissage et en test) · **time-based split** (si une date existe : test = période la plus récente) · leave-one-out (≤ 1 000 lignes) |
| Test size | 20 % | 10–40 % |
| Primary metric | R² / balanced accuracy si déséquilibre / accuracy sinon / ROC AUC en binaire | Toutes les métriques du problème : R : R², MAE, RMSE, MAPE, médiane des erreurs absolues, max error, Poisson / Gamma deviance ; C : accuracy, balanced accuracy, F1 (macro / pondéré), précision, rappel, ROC AUC, PR AUC, log loss, Brier, MCC, κ de Cohen |
| Seed | 42 | entier |
| Training rows | 200 000 au plus (échantillon reproductible, stratifié) | toutes les lignes ; nombre fixe |

Avec la validation croisée, chaque métrique est affichée « moyenne ± écart-type sur k plis » et le modèle final est réentraîné sur tout l'apprentissage.

## Critères d'acceptation

- **Catalogue déclaratif** : `domain/ml/catalog/` — un module par famille ; chaque modèle = (identifiant, famille, tâches, description, badges, profil, liste de réglages avec niveau, type, bornes, échelle, défaut ou fonction de défaut, justification, dépendances entre réglages, incompatibilités). Le frontend construit le menu et le tiroir **à partir du catalogue servi par l'API** (`GET /ml/catalog`) : ajouter un modèle ne demande aucun code d'interface.
- **Validation des réglages** côté API (bornes, combinaisons) → 422 avec un message lisible ; le frontend bloque les mêmes combinaisons (même source).
- **Défauts adaptatifs** testés : GIVEN 3 000 lignes THEN XGBoost profondeur 4 ; GIVEN 500 000 lignes THEN learning rate 0,05 ; GIVEN k-NN sur 10 000 lignes THEN k = 50 (√n borné), impair en binaire.
- **Recommandations** : règles testées (petit dataset < 1 000 lignes → linéaire / logistique + Random forest ; beaucoup de catégories ou de vides → boosting à catégories natives ; > 100 000 lignes → boosting ou SGD, pas de SVM à noyau).
- **Early stopping** : jeu de validation interne (10 % de l'apprentissage), jamais le test (test automatisé) ; nombre d'itérations retenu et courbe d'apprentissage affichés.
- **Optimiseurs** : GIVEN une logistique avec L1 THEN seuls `liblinear` et `saga` sont proposés ; GIVEN un MLP avec SGD THEN momentum et Nesterov apparaissent, β1/β2 disparaissent.
- **Exactitude** : pour chaque modèle, un test compare le résultat à l'appel direct de la bibliothèque avec les mêmes réglages et la même graine.
- **Découpages** : temporel → aucune ligne de test antérieure à une ligne d'apprentissage ; par groupes → aucun groupe des deux côtés (tests automatisés).
- **Durée** : estimation affichée avant l'entraînement pour les modèles marqués lents (à partir d'un entraînement sur un petit échantillon) ; tout entraînement est annulable.

## Dépendances

- `scikit-learn` (déjà requis en 016) couvre toutes les familles sauf XGBoost, LightGBM, CatBoost.
- `xgboost` : à valider (variante CPU dans l'image Docker si le poids l'impose).
- `lightgbm` (léger) et `catboost` (lourd, ~100 Mo) : **optionnels** — l'image Docker standard les inclut ou non selon le poids mesuré ; s'ils sont absents, ils restent visibles avec « Not installed in this build » et la commande pour les ajouter en local.
- Coefficients avec p-values : `statsmodels` (déjà requis par les séries temporelles).

## Hors scope

Réseaux profonds (PyTorch), modèles de séries temporelles dans ce module (voir 015), prédiction par lots sur un nouveau fichier, export du modèle hors de l'app (à planifier).
