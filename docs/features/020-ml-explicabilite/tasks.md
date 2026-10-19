# 020 — Tâches

Spec : [spec.md](spec.md).

## Choix de réalisation

- **Lignes d'évaluation enregistrées dans le run** (`evaluation_rows` : numéros de ligne du test, ou de toutes les lignes en validation croisée ; 10 000 au plus, tirées avec graine) : l'explication recharge exactement ces lignes avec les filtres du run. Un run antérieur à 020 demande d'être réentraîné.
- **Calcul à la demande, en tâche de fond, mis en cache** (`datasets/<id>/ml/<run>.explain.json`) : `GET …/runs/{run}/explanation` renvoie l'explication, ou lance le calcul et renvoie « running » ; le frontend interroge jusqu'à « done ».
- **Permutation importance** sur les colonnes **d'origine** (le pipeline complet est permuté colonne par colonne : one-hot et parties de date regroupées d'office), métrique principale du run, 5 répétitions, graine 42.
- **SHAP sans le paquet `shap`** : forme close φⱼ = βⱼ (zⱼ − E[zⱼ]) pour les modèles linéaires (régression, GLM, binaire en log-odds), regroupée par colonne d'origine ; TreeSHAP natif XGBoost (`pred_contribs`) / LightGBM (`pred_contrib`) écrit mais testé seulement si le paquet est installé (`importorskip`) ; ailleurs (forêts, HistGB, k-NN, SVM, MLP, NB, multiclasse) : « not available for this model », la permutation et la dépendance partielle restent.
- **Dépendance partielle** : `sklearn.inspection.partial_dependence` sur le pipeline, 8 variables les plus importantes, 30 points entre P5 et P95 ou 20 modalités, 1 000 lignes ; binaire = probabilité de la classe positive, multiclasse = une courbe par classe ; distribution de la variable sous la courbe. ICE reporté.
- **Arbre de décision** : structure exportée jusqu'à la profondeur 4 (dépliable).
- **Waterfall** d'une ligne : φ conservés pour 2 000 lignes au plus, dont toutes celles du tableau Predictions ; 10 contributions + « n other features ».
- **Corrélations** : paires de colonnes d'origine avec |r|, V de Cramér ou η > 0,8 (moteur d'association de 017).

## Tâches

- [x] T1 — `evaluation_rows` dans le run.
- [x] T2 — `domain/ml/explain.py` : permutation, SHAP linéaire + natif boosting, regroupement par colonne d'origine, dépendance partielle, arbre, corrélations, phrases de lecture.
- [x] T3 — Service / API : job, cache, endpoint ; tests (somme des φ + base = prédiction brute, regroupement one-hot, permutation, PD, arbre, cache).
- [x] T4 — UI : onglet Explain (permutation avec intervalles, beeswarm, lecture, PD + distribution, arbre, corrélations) ; waterfall au clic d'une ligne des prédictions.
- [x] T5 — Docs, vérifications, navigateur, commit.

## Découvertes

- Contrôle navigateur (typing_traps, revenu) : le waterfall montrait `age` et `birth_year` à ±1,5 × 10⁷ qui s'annulent — l'âge se déduit de la date de naissance et la régression non pénalisée gonfle les deux coefficients. Deux corrections : les paires liées incluent les dates (prises comme du temps), et la règle de préparation R-SEL-07 aussi (une date et un nombre presque identiques : la colonne la moins liée à la cible est exclue pour les modèles linéaires non pénalisés).
- Lecture des dates : « Later birth_year pushes the prediction down » au lieu d'une modalité par date ; étiquettes de date sans « 00:00:00 ».
- TreeSHAP XGBoost / LightGBM : code en place, test `importorskip` (paquets non installés).
