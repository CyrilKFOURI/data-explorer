# 020 — Machine learning : explicabilité

## Objectif

Comprendre **pourquoi** le modèle prédit ce qu'il prédit : quelles variables comptent vraiment, dans quel sens, et pour une ligne donnée, ce qui a poussé la prédiction vers le haut ou vers le bas. Référence : [11-machine-learning.md](../../pages/11-machine-learning.md).

## User stories

1. L'onglet **Explain** s'ouvre sur la **permutation importance** : de combien le score se dégrade quand on mélange chaque variable (barres avec intervalle sur 5 répétitions), calculée sur le jeu de test.
2. **SHAP global** : un graphique en essaim (beeswarm) — une ligne par variable, un point par observation, couleur = valeur de la variable — et sa lecture (« high mileage pushes the price down »).
3. **Dépendance partielle** : je choisis une variable et je vois l'effet moyen de ses valeurs sur la prédiction (courbe pour une numérique, barres pour une catégorie), avec la distribution de la variable en dessous.
4. **Explication d'une ligne** : dans l'onglet Predictions, je clique une ligne → un graphique en cascade (waterfall) part de la prédiction moyenne et ajoute la contribution de chaque variable jusqu'à la prédiction de cette ligne ; une phrase résume les trois plus fortes.
5. Les variables très corrélées entre elles sont signalées (« mileage and age are strongly linked: their importance is shared between them »).

## Critères d'acceptation

- **Permutation importance** : `sklearn.inspection.permutation_importance` sur le jeu de test (5 répétitions, graine fixe, 10 000 lignes au plus, signalé), avec la métrique principale du problème.
- **SHAP sans le paquet `shap`** :
  - boosting : contributions exactes TreeSHAP natives — XGBoost (`pred_contribs=True`), LightGBM (`pred_contrib=True`), CatBoost (`ShapValues`) ;
  - modèles linéaires et GLM : forme close φ_j = β_j (x_j − E[x_j]) sur les variables préparées (échelle du lien : log-odds, log) ;
  - autres modèles (forêts, arbres, k-NN, SVM, MLP, Naive Bayes…) : pas de SHAP — permutation importance et dépendance partielle, qui fonctionnent pour tous ; c'est indiqué clairement (à revoir si le paquet `shap` est accepté plus tard) ;
  - arbre de décision : l'arbre lui-même est affiché (profondeur 4 dépliable), c'est son explication ;
  - les contributions des colonnes one-hot sont regroupées par variable d'origine ;
  - GIVEN un modèle XGBoost THEN pour chaque ligne, somme des contributions + valeur de base = prédiction brute (à 1e-5 près).
- **Beeswarm** : 2 000 lignes au plus (échantillon signalé), 15 variables au plus (les plus importantes), le reste regroupé.
- **Dépendance partielle** : `sklearn.inspection.partial_dependence` sur une grille de 30 points (numériques, entre percentiles 5 et 95) ou les 20 modalités principales ; ICE (courbes individuelles, 50 lignes) en option.
- **Waterfall** : 10 contributions au plus, le reste regroupé en « 12 other features » ; en classification, l'échelle (probabilité ou log-odds) est indiquée.
- **Corrélations** : paires de variables explicatives avec |r| ou V de Cramér > 0,8 signalées (réutilise le moteur de 007).
- **Coût** : calculs à la demande, à l'ouverture de l'onglet, en job de fond, mis en cache par run.

## Hors scope

LIME, explications contrefactuelles (« que changer pour obtenir l'autre classe »), interactions SHAP.
