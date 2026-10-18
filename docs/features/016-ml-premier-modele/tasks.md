# 016 — Machine learning : page, cible, premier modèle en un clic : tâches

## Backend
- [x] Dépendance `scikit-learn` (accord donné)
- [x] `domain/ml/data.py` : colonnes typées à travers les filtres, 200 000 lignes au plus (échantillon reproductible)
- [x] `domain/ml/target.py` : problème déduit (régression, binaire, multiclasse) ou raison du refus (identifiant, texte, date, > 50 % vide, catégorie quasi unique)
- [x] `domain/ml/preparation.py` : moteur de règles nommées de 017 (sélection, fuite de cible dont séparation parfaite par un seuil, imputation + indicateur, log1p / Yeo-Johnson, échelle standard / robuste, one-hot / target encoding croisé, ordinal selon l'ordre validé, dates en parties et sin/cos, colinéarité) ; pipeline scikit-learn ajusté sur l'apprentissage seulement
- [x] `domain/ml/models.py` : catalogue déclaratif (régression linéaire : aucune / Ridge / Lasso ; logistique : C, équilibrage auto si classe minoritaire < 20 %), défauts justifiés, validation des réglages
- [x] `domain/ml/train.py` : 80 / 20 (stratifié), scores vs référence naïve, prédit vs réel, résidus, coefficients (IC, p, VIF, par unité), Breusch–Pagan ; AUC, matrice de confusion, rapport par classe, ROC, PR, calibration, probabilités pour le seuil ; odds ratios
- [x] Module `modules/ml` : table `ml_runs` (migration 0005), résultat JSON et pipeline `joblib` dans le dossier du dataset, entraînement en tâche de fond, historique, export CSV des prédictions
- [x] Tests : 9 tests de domaine (données synthétiques avec tous les pièges), 4 tests d'API

## Frontend
- [x] Page `/d/$datasetId/ml` (module « dataset ») : « What do you want to predict? » (colonnes suggérées, colonnes impossibles grisées avec la raison)
- [x] Entraînement automatique du modèle de référence au premier choix d'une cible ; Train avec les réglages essentiels (seuls les réglages modifiés sont envoyés)
- [x] Résumé de la préparation (décisions et raisons), validation, historique des runs (★ le meilleur)
- [x] Résultats : verdict en une phrase (dont « pas mieux que la référence », conseil Ridge en cas de surapprentissage), scores, onglets Performance / Features / Predictions, curseur de seuil en binaire
- [x] Tests : page et verdicts

## Écarts assumés
- Une seule table `ml_runs` (pas de `ml_experiments`) : un run porte sa cible ; la configuration de cible arrive avec 018.

## Vérification
- [x] Navigateur : `typing_traps` price_eur (régression, R² négatif honnêtement signalé, Ridge en run #2), is_active (binaire, AUC 0,55 → « pas mieux que la classe majoritaire »)
- [x] Constaté et corrigé au navigateur : `zip_code` (598 valeurs pour 600 lignes) proposé comme cible ; verdict trop flatteur pour un classifieur proche du hasard ; menus de réglage sans nom accessible
