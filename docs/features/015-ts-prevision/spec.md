# 015 — Séries temporelles : prévision

## Objectif

Prévoir la série sur un horizon choisi, avec des modèles simples et honnêtes, **comparés sur une validation glissante** pour que l'utilisateur voie lequel prévoit vraiment le mieux — et de combien il bat une prévision naïve. Référence : [10-series-temporelles.md](../../pages/10-series-temporelles.md).

> **Méthodes** : celles décrites ci-dessous sont les méthodes cochées par défaut ; toutes les méthodes de la section listées dans [TIMESERIES_METHODS.md](../../TIMESERIES_METHODS.md) sont proposées via « + Add method », avec la même présentation (`TestResult`, options, contribution au verdict).

## User stories

1. **Forecast** propose un bouton **Run forecast** (calcul plus long, pas lancé automatiquement) avec un horizon par défaut (Day → 30, Week → 12, Month → 12, Quarter → 8, Year → 3), modifiable.
2. Les modèles sont lancés ensemble, sans réglage :
   - **Naive** (dernière valeur) et **Seasonal naive** (même période du cycle précédent) — les références ;
   - **ETS** (lissage exponentiel, tendance et saison choisies par AIC) ;
   - **ARIMA** (ordres choisis automatiquement, saisonnier si une saison existe).
3. Un tableau classe les modèles par erreur de validation (MAE, RMSE, MAPE si toutes les valeurs > 0, **MASE**), avec la colonne « vs naive » (« 23 % better than seasonal naive »). Le meilleur est présélectionné.
4. Le graphique montre l'historique, la prévision du modèle choisi et son **intervalle de prévision à 80 % et 95 %** (deux bandes). Je peux afficher d'autres modèles en superposition.
5. Pour ARIMA, je vois l'ordre retenu (« ARIMA(1,1,1)(0,1,1)[52] ») et un diagnostic des résidus (Ljung–Box, réutilise 013) : « residuals look like white noise — the model captured the structure ».
6. J'exporte la prévision en CSV (période, prévision, bornes 80 % et 95 %, modèle).

## Critères d'acceptation

- **Validation glissante** (rolling origin) : k = 3 à 5 origines, chacune prévoyant l'horizon h ; erreurs moyennées. Si la série est trop courte (< 2 cycles + h), un seul découpage final, signalé.
- **MASE** : MAE / MAE de la prévision naïve saisonnière sur l'apprentissage (naïve simple sans saison) ; < 1 = meilleur que la référence.
- **ETS** : `statsmodels.tsa.holtwinters` / `ETSModel`, combinaisons additive / multiplicative (multiplicative seulement si valeurs > 0), tendance amortie ou non, sélection par AICc.
- **ARIMA automatique** sans `pmdarima` : recherche pas à pas (Hyndman–Khandakar simplifiée) sur `SARIMAX`, d par la synthèse ADF × KPSS (013), D par le test de saisonnalité (012), p, q ≤ 3, P, Q ≤ 1, sélection par AICc ; durée limitée (≤ 20 s, le meilleur trouvé est retenu, signalé).
- **Intervalles** : ceux du modèle (ETS, ARIMA) ; naïves : intervalles analytiques (σ√h pour naive).
- **Tâche de fond** : la prévision tourne comme un job (progression par modèle, annulable) ; résultat mis en cache par (série, horizon, modèles).
- **Tests** : série saisonnière synthétique → Seasonal naive et ETS battent Naive ; MASE de Naive vaut 1 sur sa propre référence ; ARIMA retrouve l'ordre d'un AR(1) simulé ; intervalles contenant ~95 % des valeurs en validation sur données simulées.

## Hors scope

Variables explicatives (ARIMAX), Prophet, modèles neuronaux, prévision hiérarchique (toutes les séries d'un groupe).
