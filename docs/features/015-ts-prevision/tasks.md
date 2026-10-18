# 015 — Séries temporelles : prévision : tâches

## Backend
- [x] `domain/timeseries/forecast.py` : Naive ★, Seasonal naive ★, ETS automatique ★ (toutes les formes admissibles, AICc), ARIMA automatique ★ (différences par les tests, recherche pas à pas, ≤ 20 s), Drift, Mean, SES, Holt, Holt-Winters, Theta, SARIMA (ordres manuels)
- [x] Intervalles de prévision 80 % et 95 % pour chaque modèle (analytiques pour les références, sinon ceux du modèle)
- [x] Validation glissante (jusqu'à 5 origines, chacune suivie de h périodes inconnues ; une origine où un modèle manque d'historique est sautée)
- [x] Scores : MAE, RMSE, MAPE, sMAPE, MASE, RMSSE, biais, couverture 80 % / 95 %, score de Winkler ; gain par rapport à la référence naïve (toujours calculée)
- [x] Horizon par défaut selon la période, au plus un quart de la série
- [x] Ljung–Box sur les résidus du modèle final (ETS, ARIMA, Theta…)
- [x] Tâches de fond (`modules/timeseries/forecasting.py`) : progression par modèle, annulation entre deux modèles, réutilisation d'une prévision déjà calculée
- [x] Endpoints `POST …/forecast`, `GET` / `DELETE …/forecast-jobs/{id}`
- [x] Tests : 23 tests de domaine (intervalles ordonnés pour chaque modèle, modèles saisonniers meilleurs que naive, MASE ≈ 1 sur une marche aléatoire, AR(1) retrouvé, couverture, annulation), test d'API

## Frontend
- [x] Section Forecast : horizon, modèles (+ Add method), ordres SARIMA, Run forecast, progression et annulation
- [x] Graphique : historique, prévision du modèle choisi, intervalles 80 % / 95 %, autres modèles en option ; verdict ; diagnostic des résidus
- [x] Tableau des modèles (meilleur d'abord, « All metrics »), clic pour dessiner un modèle, export CSV
- [x] Test de page

## Docs
- [x] `USER_GUIDE.md`, `TIMESERIES_METHODS.md`, `PLAN.md`

## Vérification
- [x] Navigateur : `sales_timeseries` revenue mensuel (36 mois) — 4 origines, Seasonal naive meilleur, ARIMA(2,1,2), ETS(M,N,M)
- [x] Constaté et corrigé au navigateur : une seule origine de validation (exigence de deux cycles trop stricte, horizon 12 sur 36 mois) ; couverture 0 % de Seasonal naive sur une série en croissance (écart-type au lieu de l'erreur quadratique moyenne)
