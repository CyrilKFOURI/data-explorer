# 014 — Séries temporelles : volatilité, résidus, ruptures et anomalies

## Objectif

Savoir si **la variabilité change dans le temps** (hétéroscédasticité, effets ARCH), si les **résidus** se comportent bien (normalité, loi suivie), et repérer les **ruptures** (changement de niveau ou de pente) et les **anomalies** (points atypiques). Référence : [10-series-temporelles.md](../../pages/10-series-temporelles.md).

> **Méthodes** : celles décrites ci-dessous sont les méthodes cochées par défaut ; toutes les méthodes de la section listées dans [TIMESERIES_METHODS.md](../../TIMESERIES_METHODS.md) sont proposées via « + Add method », avec la même présentation (`TestResult`, options, contribution au verdict).

## User stories

1. **Volatility** s'ouvre sur la variance glissante (et l'écart-type glissant) avec un verdict : « The variability grows over time (Breusch–Pagan p < 0.001) — a log transform usually helps. »
2. Je vois les tests d'hétéroscédasticité, chacun avec son hypothèse nulle en clair, calculés sur les **résidus d'une tendance** (STL de 012, sinon régression linéaire sur le temps) :
   - **Breusch–Pagan** et **White** (la variance dépend-elle du temps ?) ;
   - **Goldfeld–Quandt** (première partie contre dernière partie) ;
   - **ARCH-LM d'Engle** (les chocs forts sont-ils suivis de chocs forts ?) ;
   - **Levene** entre fenêtres de temps égales (4 par défaut).
3. **Residuals** : histogramme et QQ-plot des résidus, les tests de normalité de la fiche variable (Shapiro–Wilk, D'Agostino, Jarque–Bera, Anderson–Darling), et l'ajustement de lois (réutilise `domain/stats/distribution_fit.py`) sur, au choix, la série, ses rendements (variations relatives) ou ses résidus.
4. **Breaks & anomalies** :
   - les **ruptures** sont tracées sur la courbe (traits verticaux), avec le niveau moyen de chaque segment et une phrase (« level jumps from 1 200 to 1 750 in March 2023 ») ; un réglage « Sensitivity » (Low · Medium · High) ;
   - les **anomalies** sont marquées en points (z-score robuste sur les résidus), listées dans une table (date, valeur, attendu, écart) ; un clic sur une anomalie filtre les lignes de cette période dans la page Data.

## Critères d'acceptation

- **Résidus** de référence : STL robuste (012) si la saisonnalité est calculable, sinon régression linéaire sur le temps ; la source est affichée.
- **Breusch–Pagan / White** : `het_breuschpagan`, `het_white` avec le temps (et le temps²) comme régresseurs ; **Goldfeld–Quandt** : `het_goldfeldquandt` (tri par le temps, 20 % central écarté) ; **ARCH-LM** : `het_arch` (retards = min(12, n/10)) ; **Levene** : `scipy.stats.levene(center="median")` entre k fenêtres.
- **Verdict de volatilité** : majorité des tests au seuil α, plus le sens (croissante / décroissante, d'après la pente de l'écart-type glissant) ; suggestion Log si la variabilité croît avec le niveau (corrélation niveau × écart-type glissant > 0,5) et toutes les valeurs > 0.
- **Ruptures** : PELT (coût gaussien sur la moyenne, et option moyenne + variance) implémenté sur numpy, pénalité BIC × facteur de sensibilité (High 0,5 · Medium 1 · Low 2), segment minimal = max(5, période saisonnière) ; série désaisonnalisée si une saisonnalité existe. GIVEN une série en marches connue THEN les ruptures sont retrouvées à ± 2 périodes. Si l'implémentation dépasse ~150 lignes, reconsidérer la dépendance `ruptures` (à demander).
- **Anomalies** : |résidu − médiane| / (1,4826 × MAD) > 3,5 (réglable 3 / 3,5 / 4) ; au plus 50 listées (les plus fortes).
- **Normalité / lois** : mêmes implémentations et mêmes `TestResult` que la fiche variable (pas de duplication).
- **Tests** : bruit homoscédastique (aucun test ne rejette), bruit à variance croissante (BP, White, GQ rejettent), processus ARCH(1) simulé (ARCH-LM rejette), série en marches (ruptures), pics injectés (anomalies).

## Hors scope

Modèles GARCH estimés, ruptures multivariées, détection en ligne.
