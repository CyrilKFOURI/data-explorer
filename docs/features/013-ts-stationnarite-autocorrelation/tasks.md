# 013 — Séries temporelles : stationnarité et autocorrélation : tâches

## Backend
- [x] `domain/timeseries/stationarity.py` : transformations (aucune, log, différence, différence saisonnière, log + différence, différence ×2, saisonnière + différence)
- [x] ADF ★ et KPSS ★ (statsmodels) ; Phillips–Perron ★, DF-GLS et ratio de variance (Lo–MacKinlay robuste) écrits sur numpy, p-values de MacKinnon (sans `arch`, non validé) ; Zivot–Andrews et RUR (statsmodels)
- [x] Synthèse ADF × KPSS ; tests autour d'une tendance (`ct`) quand la force de tendance STL > 0,6 ; suggestion de la transformation la plus simple jugée stationnaire (2 différences au plus), toujours égale à la transformation qu'elle nomme
- [x] `domain/timeseries/autocorrelation.py` : ACF, PACF (Yule-Walker, OLS, Burg), bande ± 1,96/√n, lecture guidée (décroissance lente, pics saisonniers, coupure de la PACF → AR(p), bruit blanc)
- [x] Ljung–Box ★, Durbin–Watson ★, Box–Pierce, Breusch–Godfrey, runs, points de retournement, Bartels
- [x] Endpoints `…/stationarity?transform&methods` et `…/autocorrelation?transform&methods&pacf`
- [x] Tests : 30 tests de domaine (bruit blanc, marche aléatoire, AR(2), série saisonnière, série intégrée deux fois ; PP sans retard = DF), tests d'API

## Frontend
- [x] Sections Stationarity et Autocorrelation (sommaire, verdict court + phrase complète), sélecteur de transformation avec la suggestion marquée, partagé par les deux sections
- [x] Série transformée, ACF / PACF en barres avec bande de significativité, choix de la méthode PACF
- [x] Rangées « Methods » (7 + 7 méthodes) ; chargement à l'arrivée à l'écran, ou 2 s après l'affichage (onglet en arrière-plan)
- [x] Test de page (verdicts, suggestion, transformation dans l'URL et envoyée à l'autocorrélation)

## Docs
- [x] `USER_GUIDE.md`, `TIMESERIES_METHODS.md`, `PLAN.md`

## Vérification
- [x] Navigateur : `sales_timeseries` revenue — non concluant brut, suggestion « Seasonal + difference » qui rend la série stationnaire ; AR(2) lu sur la PACF
- [x] Constaté et corrigé au navigateur : la suggestion appliquait deux différences en affichant « Difference » ; les sections du bas ne se chargeaient pas dans un onglet en arrière-plan
