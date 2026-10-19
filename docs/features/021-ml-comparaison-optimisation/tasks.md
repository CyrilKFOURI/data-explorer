# 021 — Tâches

Spec : [spec.md](spec.md).

## Dépendances (validées le 2026-10-19)

`optuna` (+ SQLAlchemy, Alembic, colorlog, tqdm), `cmaes` (échantillonneur CMA-ES), `xgboost` (Windows / macOS) et `xgboost-cpu` (Linux, donc l'image Docker : sans CUDA), `lightgbm` ; `libgomp1` dans l'image (OpenMP). CatBoost reste absent (≈ 100 Mo) : « Not installed in this build ». Poids de l'image à mesurer au prochain `docker build` (Docker Desktop arrêté ce jour).

## Choix de réalisation

- **Comparer des modèles** : un job lance l'un après l'autre les modèles cochés (défaut : un par famille adaptée au problème), chacun crée un run ordinaire ; même validation, même graine, même préparation, même découpage (il ne dépend que de la cible et de la graine) ; un échec n'arrête pas les autres ; progression par modèle.
- **Comparer des runs** : cases dans la liste des runs ; comparables = même cible, même découpage en classes, même validation (méthode, taille du test, plis, graine, lignes) ; sinon case grisée avec la raison. Vue côte à côte : métriques, réglages qui diffèrent surlignés, prédit vs réel superposés (régression) ou courbes ROC (binaire). La validation des runs est ajoutée à `ml_runs` (migration 0007).
- **Optimiser** : Optuna sur les lignes d'apprentissage seulement (validation croisée 3 plis, élagage pli par pli), jamais le test ; le meilleur réglage devient un run ordinaire avec « Use these settings » (le test n'est vu qu'une fois, à ce moment-là). Espaces de recherche déclarés par modèle dans le catalogue (`catalog/spaces.py`), modifiables (bornes, échelle, réglage figé). Budget : 1 · 5 · 15 min ou un nombre d'essais ; arrêt manuel en gardant le meilleur. Échantillonneurs : TPE (défaut), aléatoire, grille, CMA-ES, NSGA-II ; élagage : médian (défaut), successive halving, Hyperband, aucun. Référence « réglages par défaut » évaluée dans les mêmes plis → gain affiché. Importance des réglages (fANOVA) à partir de 20 essais terminés. Essais enregistrés (`ml_tunings`, `ml_trials`).
- La préparation (017) est ajustée dans chaque pli ; le rééquilibrage et la suppression d'aberrantes ne sont pas rejoués dans les plis de l'optimisation (ils le sont au run final).

## Tâches

- [x] T1 — Dépendances, Dockerfile, SHAP natif XGBoost / LightGBM vérifié (meilleure itération).
- [x] T2 — Espaces de recherche par modèle ; job d'optimisation (échantillonneurs, élagage, budget, arrêt, défauts, importance, essais en base).
- [x] T3 — Job de comparaison de modèles ; validation dans `ml_runs` ; API.
- [x] T4 — Tests : espace et bornes, budget, arrêt, jamais le test, gain, importance, comparaison (mêmes lignes, échec isolé), comparabilité des runs.
- [x] T5 — UI : Compare models, comparaison de runs côte à côte, Tune (budget, expert, espace de recherche, suivi en direct, arrêt, résultat, Use these settings).
- [x] T6 — Docs, vérifications, navigateur, commit.

## Découvertes

- Les tests réels des boostings ont trouvé un écart du SHAP natif XGBoost : avec l'arrêt anticipé, `predict` s'arrête à la meilleure itération mais le booster brut utilisait tous les arbres → `iteration_range` (et `num_iteration` pour LightGBM).
- L'espace de recherche du MLP (couches cachées, un réglage texte) était refusé par la vérification des bornes → les réglages texte acceptent toute valeur que le modèle valide.
- Interface : la comparaison affichait « Done » avant la première réponse du suivi ; même défaut corrigé dans *Tune*.
- Navigateur : un run « elastic net » faisait planter la page (texte `ml.option.elasticnet` absent). Troisième plantage de ce type (clés de texte construites à l'exécution) : `t()` affiche désormais la clé au lieu de casser la page (avertissement en développement), et la clé manquante est ajoutée.
- Verdict d'une régression sans gain réel (R² négatif mais MAE à peine meilleure que la moyenne) : il disait « explains -1 % … 0 % better » ; il dit désormais « does no better than always predicting the average ».
- Données de test (typing_traps, revenu) : R² des défauts en validation croisée -0,15 (régression simple, 43 entrées pour ~350 lignes : sur-apprentissage) ; l'optimisation trouve un elastic net fortement pénalisé, +0,14 de R².
