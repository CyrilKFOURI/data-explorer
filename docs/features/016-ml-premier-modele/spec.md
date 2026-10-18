# 016 — Machine learning : page, cible, premier modèle en un clic

## Objectif

Poser le module ML : page `/d/:id/ml`, choix de la **cible** (seule décision obligatoire), type de problème déduit, variables explicatives et préparation automatiques, et un **modèle de référence** (régression linéaire ou logistique) entraîné aussitôt, avec des résultats lisibles et un historique des runs. Référence : [11-machine-learning.md](../../pages/11-machine-learning.md).

## User stories

1. J'ouvre **Machine learning** dans la barre latérale : « What do you want to predict? » et la liste des colonnes, les candidates suggérées en tête.
2. Je choisis `price` : le problème est reconnu (« Regression — predicts a number »), un modèle **Linear regression** s'entraîne automatiquement et le résultat s'affiche en quelques secondes. Je n'ai rien réglé.
3. Je choisis `churned` (oui / non) : « Binary classification », **Logistic regression** entraînée automatiquement.
4. Je vois les **réglages essentiels** du modèle et je peux les changer, puis cliquer **Train** (ou Ctrl+Enter).
5. Une ligne **Preparation · Automatic** résume ce qui a été fait (colonnes gardées, écartées et pourquoi) ; l'éditeur complet arrive en 017.
6. Les résultats commencent par une phrase, puis les métriques face à une **référence naïve**, puis les onglets Performance, Features, Predictions.
7. Chaque entraînement s'ajoute aux **Runs** (modèle, score principal, durée) ; un clic réaffiche un run précédent.
8. J'exporte les prédictions du jeu de test en CSV.

## Cible et type de problème

| Type de la cible | Problème | Modèle de référence |
|---|---|---|
| Numérique continue ou discrète (> 10 valeurs distinctes) | Régression | Linear regression |
| Booléen, ou catégorie à 2 modalités | Classification binaire | Logistic regression |
| Catégorie nominale ou ordinale, 3 à 20 modalités | Classification multiclasse | Logistic regression (multinomiale) |
| Numérique discrète ≤ 10 valeurs (ex. note 1–5) | Régression par défaut, avec la suggestion « Predict as classes? » | — |
| Catégorie > 20 modalités | Proposée avec avertissement : les 19 plus fréquentes + « Other » | — |

Non proposées comme cible : identifiants, texte libre, dates, colonnes ignorées, colonnes vides à plus de 50 % (avertissement si 10–50 %). Les lignes sans cible sont écartées (nombre affiché).

## Préparation des données

Entièrement automatique, par le moteur de règles de [017](../017-ml-preparation-donnees/spec.md) (sélection des variables, fuite de cible, imputation, encodage, échelle, dates, déséquilibre), ajusté sur l'apprentissage seulement. 016 livre le moteur avec les règles nécessaires aux modèles linéaires et une ligne de résumé en lecture seule (« Preparation · Automatic · 18 columns → 41 model inputs ») ; 017 complète toutes les règles et l'éditeur.

## Réglages du modèle de référence

Niveau 1 (essentiels) seulement ; les niveaux 2 et 3 et le tiroir Settings arrivent avec [019](../019-ml-catalogue-modeles/spec.md).

| Modèle | Essentiels |
|---|---|
| Linear regression | Regularization : None · Ridge · Lasso (défaut None) ; Strength (si Ridge/Lasso, défaut 1,0, échelle log) |
| Logistic regression | Regularization strength C (défaut 1,0) ; Balance classes (auto : activé si la classe minoritaire < 20 %) |

Validation par défaut : **80 / 20**, stratifiée en classification, graine 42. Lignes d'apprentissage : **200 000 au plus**, échantillon reproductible signalé (« Use all rows » en 019).

## Résultats

- **Régression** : R², MAE, RMSE, MAPE (si toutes les valeurs > 0) ; référence = prédire la moyenne d'apprentissage ; « vs average » = 1 − MAE / MAE_référence. Graphiques : prédit vs réel (diagonale), résidus vs prédit, histogramme des résidus. Linéaire : table des coefficients (estimation, erreur type, IC 95 %, p, sur variables standardisées et dans l'unité d'origine), VIF, Breusch–Pagan sur les résidus (« the error grows with the predicted value »).
- **Classification** : accuracy, balanced accuracy, F1 macro, ROC AUC (binaire ; un-contre-tous en multiclasse), log loss ; référence = classe majoritaire. Matrice de confusion (effectifs / % par ligne), précision / rappel / F1 / support par classe, ROC et PR (binaire), courbe de calibration ; **curseur de seuil** en binaire qui met à jour la matrice et les métriques en direct (sans réentraîner).
- **Phrase de verdict** : générée à partir du score principal et de la référence ; si le modèle ne bat pas la référence : « The model does no better than always predicting the average. The features may not carry information about the target. »

## Critères d'acceptation

- **Auto-entraînement** : le modèle de référence se lance seul au choix de la cible ; les autres entraînements sur **Train**. GIVEN un dataset de 5 M lignes × 30 colonnes WHEN je choisis une cible THEN un résultat s'affiche en moins de 10 s (échantillon de 200 000 lignes).
- **Exactitude** : GIVEN des données de référence THEN coefficients, R², MAE, AUC… égalent scikit-learn / statsmodels appelés directement.
- **Pas de fuite** : la préparation est ajustée sur l'apprentissage uniquement (test : une colonne dont la moyenne ne se calcule que sur le test ne doit pas influencer l'apprentissage).
- **Fuite de cible** : GIVEN une colonne copie de la cible THEN elle est exclue avec la raison « looks like it contains the answer ».
- **Jobs** : l'entraînement est un job de fond (progression, annulation, `refetchIntervalInBackground: true`).
- **Persistance** : tables `ml_experiments` (dataset, cible, problème, configuration de cible) et `ml_runs` (modèle, réglages, métriques, durée, statut, chemin du modèle sérialisé `joblib` dans le workspace) ; migration SQLite ; suppression avec le dataset.
- **Module** : déclaré dans les registres ; actif dès qu'une colonne peut servir de cible.
- **Filtres** : les filtres globaux s'appliquent (affiché : « trained on 12 400 filtered rows »).
- **Dépendance** : `scikit-learn` (à valider ; poids mesuré dans l'image Docker).

## Hors scope

Éditeur de préparation (017) ; cible en classes (018) ; catalogue de modèles, réglages avancés et expert, validation croisée (019) ; explicabilité (020) ; comparaison et optimisation (021) ; prédire sur un nouveau fichier.
