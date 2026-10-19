# 019 — Tâches

Spec : [spec.md](spec.md).

## Choix de réalisation

- **Aucune dépendance ajoutée** : XGBoost, LightGBM et CatBoost sont déclarés dans le catalogue avec leurs réglages, et affichés « Not installed in this build » tant que le paquet est absent (détection `importlib.util.find_spec`). Les installer se fera sur accord (CLAUDE.md : pas de dépendance sans demander).
- **Catalogue déclaratif** `domain/ml/catalog/` : un module par famille ; un modèle = identifiant, famille, tâches, description, badges, profil (017), réglages (niveau, groupe, type, bornes, échelle log, défaut calculé sur les données, justification, nom technique, `shown_when`), **règles de compatibilité** déclaratives (« quand `penalty` = L1, `solver` ∈ {liblinear, saga} ») servies telles quelles au frontend, qui désactive les mêmes options avec la même raison.
- Les modèles sans probabilités (SVM linéaire, ridge classifier, perceptron, SGD hinge) sont **calibrés** (`CalibratedClassifierCV`, 3 plis) pour garder ROC, seuil et log loss.
- scikit-learn 1.9 : la pénalité de la logistique passe par `l1_ratio` (0 = L2, 1 = L1) et `C = ∞` pour « none » ; le Passive-aggressive (déprécié) est un SGD `learning_rate="pa1"` ; « one-vs-rest » via `OneVsRestClassifier`.
- **Validation** : split aléatoire (stratifié), k-fold, k-fold répété, k-fold par groupes (stratifié en classification), split temporel (test = période la plus récente), leave-one-out (≤ 1 000 lignes). Avec une validation croisée, les graphiques et le tableau de prédictions utilisent les **prédictions hors-pli** (chaque ligne prédite par un modèle qui ne l'a pas vue), les scores sont « moyenne ± écart-type sur k plis », et le modèle enregistré est réentraîné sur toutes les lignes. Préparation, rééquilibrage et suppression d'aberrantes sont refaits dans chaque pli.
- Métrique principale au choix parmi toutes celles du problème (R² · MAE · RMSE · MAPE · médiane des erreurs absolues · erreur max ; accuracy · balanced accuracy · F1 macro / pondéré · précision · rappel · ROC AUC · PR AUC · log loss · Brier · MCC · κ de Cohen).
- **Lignes** : 200 000 par défaut (échantillon reproductible), toutes, ou un nombre fixe.
- Limites dures pour les modèles en O(n²)–O(n³) : processus gaussien ≤ 5 000 lignes d'apprentissage, kernel ridge ≤ 10 000, SVM à noyau ≤ 50 000 (badge *Slow* au-delà de 10 000) ; au-delà, le modèle est grisé avec sa raison.
- Importances : `feature_importances_` (arbres, forêts, boosting) dans l'onglet Features quand il n'y a pas de coefficients ; coefficients sans p-values pour les autres modèles linéaires.
- Le tiroir **Settings** (panneau droit) remplace la fenêtre pour Model · Optimizer (expert) · Validation · Rows ; l'onglet Preparation du tiroir ouvre l'éditeur de 017.

## Tâches

- [x] T1 — Paquet `catalog/` : types, règles, résolution et validation des réglages (bornes, types, règles → 422 lisible), défauts adaptatifs, badges, limites, disponibilité, recommandations.
- [x] T2 — Familles : linéaires (OLS/Ridge/Lasso/EN, Huber, quantile, Bayesian ridge, ARD, GLM Poisson/Gamma/Tweedie, logistique, ridge classifier, perceptron, passive-aggressive, SGD), LDA/QDA, k-NN, SVM linéaire / à noyau / nu, Naive Bayes (gaussien, multinomial, complement, Bernoulli), arbre, extra tree, forêt, extra trees, bagging, HistGB, GB, AdaBoost, MLP, kernel ridge, processus gaussien, XGBoost / LightGBM / CatBoost (si installés).
- [x] T3 — Validation (méthodes, taille du test, k, répétitions, groupe, date, graine, métrique), lignes ; prédictions hors-pli ; scores ± écart-type ; modèle final sur tout.
- [x] T4 — Résultats : toutes les métriques, importances, coefficients des autres modèles linéaires.
- [x] T5 — API : `GET /modules/ml/datasets/{id}/catalog` (catalogue + recommandations calculées sur les données filtrées), `validation` sur `POST /runs` ; tests (défauts adaptatifs, règles, recommandations, chaque modèle s'entraîne, exactitude vs appel direct, découpages temporel et par groupes, early stopping interne).
- [x] T6 — UI : sélecteur de modèle (recherche, Recommended, familles, badges, raisons, « Not installed »), essentiels, tiroir Settings (Expert, onglets, groupes, nom technique, point + Reset, règles), validation et lignes, scores ± écart-type, importances.
- [x] T7 — Docs (page 11, guide, PLAN), vérifications, navigateur, commit.

## Reporté (019b) — livré, voir [tasks-019b.md](tasks-019b.md)

Durée estimée sur un petit échantillon et annulation en cours d'entraînement, courbe d'apprentissage, contraintes monotones, choix du seuil de décision sur la validation, Radius neighbours et Categorical NB (encodage dédié), Voting / Stacking (021).

## Découvertes

- Le test « chaque modèle s'entraîne sur ses problèmes » a trouvé 4 défauts corrigés : défaut de la régression quantile (pénalité 0) hors de ses bornes ; Naive Bayes multinomial / complement recevant des parties de date négatives (sin / cos) → mise à l'échelle [0, 1] pour les modèles à entrées positives (dates, codes ordinaux, `MinMaxScaler(clip=True)`) ; l'Extra tree seul refuse les vides (contrairement à la forêt) → imputation.
- La comparaison « appel direct de la bibliothèque » doit exclure le target encoding : à l'entraînement ses valeurs sont croisées (`fit_transform`), pas celles de `transform`.
- Les runs portent le nom du modèle (`label`) et le sens de leur métrique (`greater_is_better`) : le ★ trie correctement MAE ou log loss.
