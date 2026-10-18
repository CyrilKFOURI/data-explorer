# Module Séries temporelles — `/d/:id/timeseries`

> **Statut : futur (Sprint 4). Ne pas implémenter avant la V1.**
>
> **Précisé par** [10-series-temporelles.md](../pages/10-series-temporelles.md) et les specs 011 à 015 (font foi en cas d'écart).

## Configuration

Colonne de temps, une ou plusieurs séries numériques, agrégation (somme, moyenne…), fréquence (détectée, modifiable), série par groupe (ex. une série par pays), gestion des trous (laisser vide, interpoler, remplir).

## Analyses

| Famille | Contenu |
|---|---|
| Visualisation | Courbe, moyenne et écart-type glissants, zoom sur une plage, superposition de plusieurs séries, lag plot, saisonnalité (une courbe par année) |
| Décomposition | STL / classique : tendance, saisonnalité, résidu ; force de la tendance et de la saisonnalité |
| Stationnarité | ADF, KPSS, Phillips–Perron, avec une synthèse croisée (« ADF et KPSS concordent : non stationnaire ») ; suggestion de différenciation |
| **Hétéroscédasticité** | Breusch–Pagan, White, Goldfeld–Quandt (sur résidus d'une tendance), **ARCH-LM d'Engle**, variance glissante ; test de Levene entre fenêtres |
| Normalité des résidus | Mêmes tests que la fiche variable + QQ-plot des résidus |
| Loi suivie | Ajustement de lois sur la série, les rendements ou les résidus (réutilise `domain/stats/distribution_fit.py`) |
| Autocorrélation | ACF, PACF, Ljung–Box, Durbin–Watson |
| Ruptures et anomalies | Détection de points de rupture, anomalies sur résidus (z-score robuste) |
| Prévision (de base) | Naïve, saisonnière naïve, ETS, ARIMA auto ; intervalle de prévision ; validation glissante |

Chaque résultat est présenté avec un `TestResult` et une phrase d'explication, comme en V1.

## Dépendances pressenties

statsmodels, et éventuellement ruptures (points de rupture). À valider au moment du sprint.
