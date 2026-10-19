# Séries temporelles — `/d/:id/timeseries`

> Module (après la V1). **Livré : 011 à 015 (Sprint 4 terminé).** Jalons : [012](../features/012-ts-page-visualisation/spec.md) · [013](../features/013-ts-stationnarite-autocorrelation/spec.md) · [014](../features/014-ts-volatilite-ruptures/spec.md) · [015](../features/015-ts-prevision/spec.md). Intention d'origine : [modules-futurs/series-temporelles.md](../modules-futurs/series-temporelles.md).

## Rôle

Analyser **une série** en profondeur : la voir, la décomposer, tester sa stationnarité, sa mémoire, sa volatilité, ses ruptures, puis la prévoir. Chaque résultat est un `TestResult` avec un verdict en une phrase, comme partout dans l'app. C'est la vitrine « profondeur statistique » du projet.

## Principes UX

- **Rien à régler pour commencer.** La page s'ouvre déjà configurée : la seule date du dataset (ou la première), la première variable numérique ayant un rôle `amount` / `quantity` (sinon la première numérique), l'agrégation et la période par défaut de [011](../features/011-vue-temporelle/spec.md). Depuis Comparer, tout arrive prérempli.
- **Une seule série analysée à la fois.** Les tests sont univariés ; avec un groupe, un sélecteur « Series » choisit la série étudiée (« store = Paris »), et la vue d'ensemble peut les superposer.
- **Lecture de haut en bas**, comme un rapport : chaque section répond à une question et commence par sa conclusion. Un sommaire collant à gauche (ancres) permet de sauter d'une section à l'autre et affiche une pastille de verdict par section (« stationary after 1 differencing », « seasonal: weekly »).
- **Toutes les méthodes au choix.** Chaque section propose toutes les méthodes existantes pour sa question (ex. stationnarité : ADF, KPSS, Phillips–Perron, DF-GLS, Zivot–Andrews, ratio de variance…) ; les plus fiables sont cochées par défaut, les autres s'ajoutent par « + Add method ». Catalogue complet et règle d'interface : [TIMESERIES_METHODS.md](../TIMESERIES_METHODS.md).
- **Calculs à la demande** : les sections se calculent quand elles entrent dans l'écran (les plus coûteuses — prévision — sur bouton).

## Disposition

```
┌ Barre de configuration (une ligne, collante) ─────────────────────────────────────────┐
│ Time [order_date ▾]  Value [revenue ▾]  Weekly ▾  Sum ▾  Group [none ▾]  Gaps: leave ▾ │
└───────────────────────────────────────────────────────────────────────────────────────┘
┌ Sommaire ─┐ ┌ Contenu ─────────────────────────────────────────────────────────────────┐
│ Overview ●│ │ 1. Overview — courbe + moyenne/écart-type glissants, zoom, plage         │
│ Season.  ●│ │ 2. Seasonality — profils par année, par mois, par jour de semaine        │
│ Decomp.  ●│ │ 3. Decomposition — tendance, saisonnalité, résidu (STL)                  │
│ Station. ●│ │ 4. Stationarity — ADF, KPSS, PP, synthèse, différenciation               │
│ Memory   ●│ │ 5. Autocorrelation — ACF, PACF, Ljung–Box, Durbin–Watson                 │
│ Volatil. ●│ │ 6. Volatility — variance glissante, ARCH-LM, Breusch–Pagan…              │
│ Breaks   ●│ │ 7. Breaks & anomalies — ruptures, points atypiques                       │
│ Forecast ●│ │ 8. Forecast — modèles, validation glissante, horizon                     │
└───────────┘ └──────────────────────────────────────────────────────────────────────────┘
```

## Barre de configuration

| Champ | Défaut | Notes |
|---|---|---|
| Time | seule date / première date | Les colonnes date et date-heure seulement |
| Value | rôle `amount`/`quantity`, sinon 1re numérique | Numériques seulement |
| Period | Auto (011) | Day · Week · Month · Quarter · Year (+ Hour si date-heure) |
| Aggregate | Sum (montants, volumes) / Mean | Sum · Mean · Median · Min · Max · Count |
| Group | aucun | Catégorie ; ajoute le sélecteur « Series » (8 séries au plus) |
| Gaps | Leave empty | Leave empty · Interpolate (linéaire) · Fill with 0 · Carry forward. Les tests qui exigent une série complète (ACF, STL, ARIMA) interpolent d'office et le disent. |

Tout est dans l'URL. Les filtres globaux s'appliquent (le bandeau filtres reste visible).

## Réglages de la vue d'ensemble (revus le 2026-10-19)

Au-dessus du graphique, deux lignes nommées au lieu d'une suite de contrôles :

- **Rolling means** : une pastille par moyenne mobile, avec la couleur de sa courbe et son nom complet (« 7 weeks », « 15 weeks ») ; × pour la retirer ; sans choix, une pastille pointillée « Auto · 7 weeks ». **+ Add** ouvre un petit champ avec des fenêtres suggérées selon la période (jour : 7 · 14 · 30 · 90 ; semaine : 4 · 13 · 26 · 52 ; mois : 3 · 6 · 12…) ou une valeur libre ; 5 moyennes au plus. À droite : **Position** Trailing | Centered (contrôle segmenté).
- **Show** : Values · Rolling means · ± 1σ band (autour de la première moyenne, dite dans le libellé).
- Les légendes du graphique reprennent les mêmes noms (« 7-week rolling mean », « 15-week rolling mean »).

## Anomalies (revu le 2026-10-19)

Toutes les anomalies restent marquées sur le graphique ; le tableau sous le graphique n'en montre que les **5 plus fortes**, avec « Show all 23 anomalies » (et « Show fewer » une fois déplié).

## États

- Aucune colonne date : la page est grisée dans la barre latérale avec l'infobulle « Needs a date column ».
- Moins de 8 périodes : seule la vue d'ensemble s'affiche, avec « Too few periods to analyse (8 needed) ».
- Chaque section qui ne peut pas se calculer dit pourquoi (« Seasonality needs at least two full cycles: 104 weeks, you have 61 »).

## Dépendances

`statsmodels` (l'essentiel) et `arch` (léger : Phillips–Perron, DF-GLS, ratio de variance), à valider avant 012 et 013 (poids de l'image Docker). Ruptures, tests d'homogénéité et tests de caractère aléatoire implémentés sur numpy/scipy. Détail : [TIMESERIES_METHODS.md](../TIMESERIES_METHODS.md).
