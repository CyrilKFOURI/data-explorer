# 014 — Séries temporelles : volatilité, résidus, ruptures et anomalies : tâches

## Backend
- [x] `residuals.py` : résidus = reste de STL (sinon résidus d'une droite) ; distribution des résidus, de la série ou de ses variations relatives avec **le code de la fiche variable** (statistiques, tests de normalité, densité, QQ-plot, ajustement de lois, transformations)
- [x] STL adaptée aux séries courtes (`decomposition.stl`) : lissage saisonnier constant sous 7 cycles, robuste sauf s'il dégénère (reste fait de zéros) — partagée par toutes les sections
- [x] Périodes de bord incomplètes (somme, comptage) exclues de toutes les analyses, pas seulement du test de tendance
- [x] `volatility.py` : écart-type glissant des résidus, sens, suggestion de log ; Breusch–Pagan ★, ARCH-LM ★, White, Goldfeld–Quandt, McLeod–Li, Levene, Brown–Forsythe, Bartlett, Fligner–Killeen
- [x] `breaks.py` : PELT ★ et segmentation binaire (numpy), coûts moyenne / moyenne + variance / **tendance par segments** (choisie automatiquement si la série a une tendance) ; Pettitt ★, CUSUM, Chow, Buishand, SNHT ; anomalies (z robuste ★, IQR, z glissant, filtre de Hampel)
- [x] Endpoints `…/volatility`, `…/residuals?source`, `…/breaks?search&cost&sensitivity&anomaly&threshold&methods`
- [x] Tests : 42 tests de domaine (variance croissante, ARCH(1), marches, changement de pente, tendance régulière sans fausse rupture, pics injectés, STL dégénérée), tests d'API

## Frontend
- [x] Section Volatility (résidus et écart-type glissant sur deux panneaux, méthodes)
- [x] Section Residuals : Residuals · Series · Returns, statistiques de forme, QQ-plot, panneau de normalité et ajustement de lois de la fiche variable (réutilisés)
- [x] Section Breaks & anomalies : recherche, coût, sensibilité, droites ou moyennes par segment, phrases, tests ; tableau des anomalies avec « Show rows » (filtre la page Data sur la période)
- [x] Test de page des trois sections

## Docs
- [x] `USER_GUIDE.md`, `TIMESERIES_METHODS.md`, `PLAN.md`

## Vérification
- [x] Navigateur : `sales_timeseries` revenue — résidus Student, 4 changements de pente, 16 anomalies
- [x] Constaté et corrigé au navigateur : dernière semaine incomplète (résidu −42 000) ; 8 fausses ruptures « en escalier » sur une tendance régulière ; STL robuste dégénérée (MAD = 0, 50 anomalies) ; `+` à la place de l'espace dans les dates du lien « Show rows »
