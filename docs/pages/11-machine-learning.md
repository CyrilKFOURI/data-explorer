# Machine learning — `/d/:id/ml`

> Module (après la V1). **Livré : 016, 017, 018, 019 (sauf 019b), 020.** Jalons : [016](../features/016-ml-premier-modele/spec.md) premier modèle · [017](../features/017-ml-preparation-donnees/spec.md) préparation des données · [018](../features/018-ml-cible-en-classes/spec.md) cible en classes · [019](../features/019-ml-catalogue-modeles/spec.md) catalogue de modèles, réglages, optimiseurs · [020](../features/020-ml-explicabilite/spec.md) explicabilité · [021](../features/021-ml-comparaison-optimisation/spec.md) comparaison et optimisation. Intention d'origine : [modules-futurs/machine-learning.md](../modules-futurs/machine-learning.md).

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
- **Predict as [Number | Classes] (018, livré)** : sous la cible numérique. *Classes* déplie le panneau (−/+ de 2 à 10, *Split by* avec une ligne d'explication par méthode, *Round values*, *Ignore outliers* pour Equal width, histogramme pleine largeur avec les limites — glissables à la souris et au clavier en Custom —, une ligne par classe : pastille séquentielle, nom éditable, intervalle, effectif, %, barre). Avertissements avec action (classe trop petite → « Use k − 1 classes », ex-aequo, classes fusionnées). L'entraînement part seul 600 ms après le dernier changement. Une cible discrète à ≤ 10 valeurs propose « One class per value ». Les runs en classes portent « · 3 classes » ; le ★ ne compare que des runs notés de la même façon.
- **Model [ ▾ ] et tiroir Settings (019, livré)** : le sélecteur (fenêtre cherchable) montre « Recommended for this data » (règles : < 1 000 lignes → linéaire / logistique + forêt ; > 100 000 → boosting + SGD ; sinon boosting + référence + forêt), puis les familles repliables avec description et badges ; un modèle limité par la taille des données est grisé avec sa raison ; XGBoost / LightGBM / CatBoost affichent « Not installed in this build ». Sous le modèle : les réglages essentiels ; « All settings » ouvre le tiroir droit (480 px) : Expert, Reset all, onglets Model (groupes Structure, Regularization, Sampling, Class balance, Stopping ; nom technique en mono ; point + reset), Optimizer (expert), Validation (méthode, taille du test, k, répétitions, colonne de groupe, colonne de date, métrique principale, graine), Rows (200 000 / toutes / nombre fixe) ; Train en bas. Les options interdites par une règle sont grisées avec la raison, la même que côté serveur. Résultats : « All metrics » (toutes les métriques, ± écart-type sur les plis en validation croisée) ; onglet Features : importances pour les arbres et le boosting.
- **Onglet Explain (020, livré)** : calculé en tâche de fond à la première ouverture (« Computing the explanation… »), puis gardé avec le run. Dans l'ordre : permutation importance (baisse de la métrique principale quand on mélange chaque colonne d'origine, barres ± écart-type sur 5 répétitions) ; bandeau des colonnes fortement liées (|r|, V de Cramér ou η > 0,8, dates comprises) ; SHAP en essaim (une ligne par colonne, un point par ligne, couleur = valeur basse → haute) avec ses phrases de lecture, ou la raison de son absence ; dépendance partielle (menu de colonne, courbe ou barres, distribution des lignes dessous) ; l'arbre lui-même pour un arbre de décision. **Predictions** : cliquer une ligne affiche son waterfall (moyenne → 10 contributions + « n other features » → cette ligne) et une phrase sur les trois plus fortes.
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
