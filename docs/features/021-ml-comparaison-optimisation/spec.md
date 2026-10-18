# 021 — Machine learning : comparaison des modèles et optimisation

## Objectif

Répondre vite à « quel modèle est le meilleur ici ? » et, si on le souhaite, laisser l'app **chercher les meilleurs réglages** dans un budget de temps. Référence : [11-machine-learning.md](../../pages/11-machine-learning.md).

## User stories

1. **Compare models** lance d'un coup une sélection de modèles du catalogue (019) — par défaut un par famille adaptée au problème, modifiable par cases à cocher — avec leurs défauts, sur la **même validation** ; un tableau triable les classe (score principal, autres métriques, durée) et met le meilleur en avant.
2. Dans **Runs**, je coche deux runs ou plus → vue côte à côte : métriques, réglages qui diffèrent (surlignés), graphiques superposés (prédit vs réel, ROC).
3. **Tune** (sur un modèle) lance une optimisation des réglages essentiels et avancés avec un **budget** : 1 min · 5 min · 15 min, ou un nombre d'essais. En mode Expert : choix de l'algorithme de recherche — **TPE** (défaut), **random search**, **grid search**, **CMA-ES**, **NSGA-II** (plusieurs métriques) — et de l'élagage (médian · successive halving · Hyperband · aucun).
4. Pendant l'optimisation, je vois en direct le meilleur score trouvé, la courbe des essais (score par essai, meilleur cumulé) ; je peux arrêter quand je veux et garder le meilleur.
5. À la fin : les réglages trouvés (différences avec les défauts surlignées), le gain (« +0.03 R² over defaults ») et **Use these settings**, qui crée un run avec ces réglages.
6. L'importance des réglages dans l'optimisation (« learning rate mattered most ») aide à comprendre ce qui compte.

## Critères d'acceptation

- **Comparaison** : mêmes lignes d'apprentissage et de test (ou mêmes plis) pour tous les modèles ; graine commune ; jobs exécutés l'un après l'autre avec progression par modèle ; un modèle en échec n'arrête pas les autres (erreur affichée sur sa ligne).
- **Comparaison de runs** : seuls des runs de la **même expérience** (même cible, même configuration de cible, même validation) sont comparables ; sinon, la case est grisée avec la raison.
- **Optimisation** : Optuna (échantillonneur TPE, élagage médian), validation croisée 3 plis sur l'apprentissage (jamais le jeu de test) ; espaces de recherche déclarés dans le catalogue (019), par modèle, modifiables dans un panneau « Search space » (bornes, échelle, réglages figés) (ex. XGBoost : profondeur 2–10, learning rate 0,01–0,3 log, subsample 0,5–1, colsample 0,5–1, min_child_weight 1–10 log, lambda 1e-3–10 log) ; le meilleur réglage est réévalué sur le jeu de test une seule fois, à la fin.
- **Budget** : respecté à ± 10 % ; arrêt manuel conservant le meilleur essai ; historique des essais enregistré (table `ml_trials`).
- **Importance des réglages** : `optuna.importance.get_param_importances` (fANOVA) affichée si ≥ 20 essais.
- **Dépendance** : `optuna` (à valider ; poids mesuré).

## Hors scope

Ensembles (stacking, blending), AutoML de la préparation, sélection automatique de variables.
