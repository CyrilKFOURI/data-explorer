# 013 — Séries temporelles : stationnarité et autocorrélation

## Objectif

Répondre à deux questions qui conditionnent toute modélisation : **la série est-elle stationnaire ?** (sinon, comment la rendre stationnaire) et **a-t-elle de la mémoire ?** (les valeurs passées expliquent-elles les suivantes). Référence : [10-series-temporelles.md](../../pages/10-series-temporelles.md).

> **Méthodes** : celles décrites ci-dessous sont les méthodes cochées par défaut ; toutes les méthodes de la section listées dans [TIMESERIES_METHODS.md](../../TIMESERIES_METHODS.md) sont proposées via « + Add method », avec la même présentation (`TestResult`, options, contribution au verdict).

## User stories

1. **Stationarity** commence par une synthèse croisée en une phrase : « ADF and KPSS agree: the series is not stationary. One differencing makes it stationary. »
2. Je vois le détail des trois tests (statistique, p-value, valeurs critiques, hypothèse nulle en clair) :
   - **ADF** — H0 : racine unitaire (non stationnaire) ;
   - **KPSS** — H0 : stationnaire (autour d'un niveau ou d'une tendance) ;
   - **Phillips–Perron** — H0 : racine unitaire, robuste à l'autocorrélation et à l'hétéroscédasticité.
3. Je choisis la transformation à tester : **None · Log · First difference · Seasonal difference · Log + difference** ; la courbe transformée et les tests se mettent à jour. L'app **suggère** la plus simple qui rend la série stationnaire (« Suggested: first difference »).
4. **Autocorrelation** : ACF et PACF (barres avec bande de confiance à 95 %), sur la série ou sa version transformée ; **Ljung–Box** à plusieurs retards (« values are linked up to 3 weeks back ») ; **Durbin–Watson** sur les résidus d'une tendance linéaire.
5. Une lecture guidée traduit les formes classiques : « ACF decays slowly → trend or unit root », « PACF cuts off after lag 2 → an AR(2) is a good start », « spikes every 7 lags → weekly seasonality ».

## Critères d'acceptation

- **Synthèse ADF × KPSS** (table de décision, α configurable, défaut 0,05) :

| ADF rejette H0 | KPSS rejette H0 | Verdict |
|---|---|---|
| oui | non | Stationnaire |
| non | oui | Non stationnaire (racine unitaire) |
| oui | oui | Stationnaire autour d'une tendance ou en différence : « difference-stationary or trend-stationary — try differencing » |
| non | non | Données insuffisantes pour conclure |

- **ADF** : `adfuller(autolag="AIC")`, régression `c` par défaut, `ct` si la tendance de 012 est forte (F_T > 0,6), affichée. **KPSS** : `kpss(regression="c" | "ct", nlags="auto")` ; l'avertissement « p-value hors table » de statsmodels est traduit (« p > 0.10 »). **Phillips–Perron** : `arch.unitroot.PhillipsPerron` si `arch` est accepté, sinon implémentation numpy (Z_t, variance de long terme Newey–West, valeurs critiques de MacKinnon) égale à `arch` à 1e-6 près dans les tests.
- **Suggestion de différenciation** : essaie dans l'ordre None → First difference → Seasonal difference → Log + difference (Log seulement si toutes les valeurs > 0) et retient la première transformation jugée stationnaire par la synthèse ; au plus 2 différenciations.
- **ACF / PACF** : `acf`, `pacf(method="ywm")` jusqu'à min(40, n/4) retards ; bande ± 1,96/√n ; série complétée (interpolation signalée).
- **Ljung–Box** : `acorr_ljungbox` aux retards 1, période saisonnière, 2 × période (bornés par n/5) ; verdict sur le plus petit retard significatif.
- **Durbin–Watson** sur les résidus de la régression linéaire sur le temps ; lecture (≈ 2 : pas d'autocorrélation ; < 1,5 : positive ; > 2,5 : négative).
- **Lecture guidée** : règles simples et testées (décroissance lente de l'ACF = ρ(10) > 0,5 ; coupure de la PACF = dernier retard significatif suivi de 3 non significatifs ; pics saisonniers = ACF significative au retard de la période et à ses multiples).
- **Minimum** : 20 périodes pour les tests (sinon message).
- **Tests** : bruit blanc (stationnaire, aucune autocorrélation), marche aléatoire (non stationnaire, différence suggérée), AR(2) (PACF coupée à 2), série saisonnière (pics), vs statsmodels.

## Hors scope

HEGY, cointégration, séries multivariées.
