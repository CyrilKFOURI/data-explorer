# Machine learning — `/d/:id/ml`

> Module (après la V1). **Livré : 016, 017.** Jalons : [016](../features/016-ml-premier-modele/spec.md) premier modèle · [017](../features/017-ml-preparation-donnees/spec.md) préparation des données · [018](../features/018-ml-cible-en-classes/spec.md) cible en classes · [019](../features/019-ml-catalogue-modeles/spec.md) catalogue de modèles, réglages, optimiseurs · [020](../features/020-ml-explicabilite/spec.md) explicabilité · [021](../features/021-ml-comparaison-optimisation/spec.md) comparaison et optimisation. Intention d'origine : [modules-futurs/machine-learning.md](../modules-futurs/machine-learning.md).

## Rôle

Un outil **no-code** pour entraîner, évaluer et comprendre un modèle prédictif **en un clic**, puis l'affiner aussi loin qu'on le souhaite. La seule décision obligatoire est **la variable à prédire**. Tout le reste — préparation des données, modèle, réglages, validation — a une valeur par défaut décidée par des règles explicites, justifiée, et modifiable.

## Ce qui distingue l'app des consoles ML (cloud ou autres)

- **On part d'une question, pas d'une configuration** : « What do you want to predict? ».
- **La préparation des données est faite comme par un data scientist**, par des règles nommées qui dépendent du type détecté de chaque colonne et du modèle — jamais cachée : chaque décision dit pourquoi ([017](../features/017-ml-preparation-donnees/spec.md)).
- **Les réglages sont en couches** : 2 ou 3 essentiels visibles ; tout le reste existe (jusqu'à l'algorithme d'optimisation) mais se déplie.
- **Le résultat se lit en une phrase**, face à une référence naïve.
- **Langage courant d'abord**, nom technique ensuite (en petit). Pas de jargon d'infrastructure : tout est local.
- Même identité visuelle que le reste de l'app (tokens, typographie, `TestResult`, verdicts).

## Principes UX

1. **Une seule question au départ.** Choisir la cible suffit : le problème est déduit, la préparation est automatique, et un **modèle de référence** (régression linéaire ou logistique) s'entraîne aussitôt.
2. **Trois niveaux de réglages** ([019](../features/019-ml-catalogue-modeles/spec.md)) : **Essentials** dans la colonne de gauche ; **Advanced** dans le tiroir Settings ; **Expert** (interrupteur dans le tiroir) pour l'optimiseur, les tolérances, la précision.
3. **Chaque défaut se justifie** dans une infobulle (« Depth 4 because the dataset is small »).
4. **Comparer est naturel** : chaque entraînement devient un run ; changer un réglage puis relancer montre tout de suite si c'est mieux.
5. **Pas de piège silencieux** : fuite de cible, classes rares, échantillonnage, déséquilibre, choix incompatibles sont signalés.

## Disposition

```
┌ Réglages (colonne gauche, ~320 px) ─────────────┐ ┌ Résultats ───────────────────────────────────────────┐
│ Predict    [ price ▾ ]                           │ │ Run #3 · XGBoost · 2.1 s                              │
│            [ Number | Classes ]        (018)     │ │ "Explains 82 % of the variation in price —            │
│                                                  │ │  41 % better than always predicting the average."     │
│ Model      [ XGBoost ▾ ]  Boosting ensembles     │ │  R² 0.82   MAE 1 240   RMSE 1 910                     │
│   Number of trees   1000 · early stopping        │ │ [ Performance | Features | Predictions | Explain ]    │
│   Tree depth        6                            │ │                                                       │
│   Learning rate     0.1                          │ │   graphiques de l'onglet                              │
│   All settings ▸                                 │ │                                                       │
│                                                  │ │                                                       │
│ Preparation  Automatic · 18 → 41 inputs · Edit   │ │                                                       │
│ Validation   80 / 20 split · Edit                │ │ Runs  #1 Logistic 0.61 · #2 RF 0.79 · #3 XGB 0.82 ★   │
│ Rows         200 000 of 5 M · Edit               │ └───────────────────────────────────────────────────────┘
│ [ Train ]  Ctrl+Enter                            │
└──────────────────────────────────────────────────┘
```

- **Model [ ▾ ]** ouvre le sélecteur : modèles rangés par familles (Linear models, Discriminant analysis, Nearest neighbours, Support vector machines, Naive Bayes, Trees, Bagging ensembles, Boosting ensembles, Neural networks, Kernel & probabilistic, Combinations), recherche, section « Recommended for this data », badges (*Fast*, *Interpretable*, *Handles missing values*, *Slow on this data*).
- **All settings ▸**, **Preparation · Edit**, **Validation · Edit** et **Rows · Edit** ouvrent le même **tiroir Settings** (panneau droit) sur l'onglet correspondant : Model · Optimizer (expert) · Preparation · Validation · Rows. Les résultats restent visibles derrière.
- **Preparation · Edit (017, livré)** : en attendant le tiroir de 019, l'éditeur s'ouvre dans une grande fenêtre. En tête : *Automatic / Custom*, *Reset all*, une ligne de résumé (« 9 columns → 23 model inputs · 2 excluded »), les avertissements (choix refusés et pourquoi). Onglets : **Columns** (une ligne par colonne : Use, Missing (+ indicateur), Transform, Encoding, Scaling ; valeur automatique en gris « Auto: median », choix manuel en encre normale avec un point et un bouton de remise à zéro ; options impossibles grisées avec leur raison ; ⓘ = règles appliquées ; colonnes exclues en bas avec leur raison et « Use anyway », confirmation pour une fuite suspectée) · **Selection** (8 méthodes à cocher, chacune avec son seuil, et le nombre d'entrées gardées) · **Missing & outliers** (imputation numérique par défaut, seuils, limite du one-hot, lissage, aberrantes) · **Imbalance** (classification : stratégie, répartition avant / après) · **Preview** (20 premières lignes d'apprentissage préparées, noms des entrées produites). L'aperçu se recalcule à chaque choix ; *Train* envoie les choix, enregistrés dans le run ; ouvrir un run reprend ses choix.
- **État vide** (aucune cible) : au centre, « What do you want to predict? » et une liste de colonnes cherchable ; les candidates naturelles en tête avec « Suggested ».
- **Pendant l'entraînement** : progression dans le bouton (« Training… 64 % »), annulable ; les résultats précédents restent visibles, atténués.
- **Mémoire** : la dernière cible, le dernier modèle et ses réglages sont rouverts au retour sur la page.

## Résultats (onglets)

| Onglet | Régression | Classification |
|---|---|---|
| Performance | Prédit vs réel (+ diagonale), résidus vs prédit, distribution des résidus, courbe d'apprentissage (modèles itératifs) ; linéaire : Breusch–Pagan des résidus | Matrice de confusion (effectifs / %), rapport par classe, ROC et PR (binaire), calibration ; curseur de seuil (binaire) ; classes ordonnées (018) : « exact or off by one » |
| Features | Coefficients (linéaire : IC et p) ou importance (arbres) | idem |
| Predictions | Lignes de test : réel, prédit, erreur (triable, exportable) ; clic → explication de la ligne (020) | réel, prédit, probabilité, correct ? |
| Explain (020) | Permutation importance, SHAP global et par ligne, dépendance partielle | idem |

## Dépendances

`scikit-learn` (016), `statsmodels` (déjà requis par les séries temporelles), `xgboost` (019 ; variante CPU dans l'image Docker si le poids l'impose), `lightgbm` et `catboost` optionnels selon le poids, `optuna` (021). SHAP sans le paquet `shap` (contributions natives du boosting, forme close pour les modèles linéaires). Chaque ajout se valide au moment du jalon, poids de l'image mesuré (limite CI 600 Mo).
