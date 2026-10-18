# Module Machine learning — `/d/:id/ml`

> **Statut : futur (Sprint 5). Ne pas implémenter avant la V1.**
>
> **Précisé par** [11-machine-learning.md](../pages/11-machine-learning.md) et les specs 016 à 021 (font foi en cas d'écart).

## Parcours

1. **Cible** → type de problème détecté (classification binaire ou multiclasse, régression) à partir du type de colonne.
2. **Features** : sélection par défaut expliquée (cible, identifiants, colonnes > 80 % de vides et colonnes redondantes exclues), modifiable.
3. **Préparation** : imputation (aucune pour XGBoost, qui gère les NaN nativement, ce qui est indiqué ; sinon moyenne, médiane, mode, KNN), encodage (one-hot ou ordinal selon le type), mise à l'échelle. Le tout dans un pipeline scikit-learn.
4. **Modèle** : XGBoost par défaut, hyperparamètres proposés selon la taille du dataset et le déséquilibre des classes ; autres modèles : régression linéaire / logistique, Random Forest, LightGBM, CatBoost, SVM, MLP. Panneau d'hyperparamètres dynamique.
5. **Validation** : train/test (stratifié en classification), validation croisée.
6. **Résultats** : classification → matrice de confusion, rapport par classe, ROC/AUC, courbe PR, calibration ; régression → prédit vs réel, **résidus (dont tests d'hétéroscédasticité)**, MAE, RMSE, R².
7. **Explicabilité** : importance des features, permutation importance, SHAP (global et par ligne).
8. **Comparaison** : plusieurs modèles lancés d'un coup, tableau triable ; optimisation Optuna en option avec historique des essais.

Entraînements en tâche de fond (progression), GPU utilisé si disponible (XGBoost CUDA). Expériences enregistrées (`ml_experiments`, `ml_runs`).

## Dépendances pressenties

scikit-learn, xgboost, lightgbm, catboost, shap, optuna. À valider au moment du sprint.
