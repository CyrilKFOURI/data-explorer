# 011 — Vue temporelle dans Comparer : tâches

## Backend
- [x] `domain/compare/` date × num : agrégation par période (Sum, Mean, Median, Min, Max, Count) et par groupe, en SQL ; période Auto (pas détecté, relevé au-delà de 400 périodes)
- [x] Défaut d'agrégation selon le rôle de Y (`amount`, `quantity` → Sum ; sinon Mean)
- [x] Trous : laissés vides (0 pour Sum et Count) ; moyenne et écart-type glissants (fenêtre arrière ou centrée, `min_periods`)
- [x] `domain/timeseries/trend.py` (réutilisé par 012) : Mann-Kendall (correction des ex-aequo) + pente de Sen et IC 95 % ; autocorrélation lag-1 pour la mise en garde
- [x] API : paramètres `period`, `agg`, `window`, `align` sur `GET /datasets/{id}/compare`
- [x] Tests : agrégations, trous, rolling vs pandas (fixture), Mann-Kendall / Sen vs valeurs de référence, < 8 périodes, groupes, perf 5 M (`-m slow`)

## Frontend
- [x] Vue **Time series** : courbe, moyenne glissante, bande ± σ ; une courbe par groupe
- [x] Barre d'options (Period, Aggregate, Window, Show) dans l'URL ; libellé résumé sous le titre
- [x] Panneau de test : Mann-Kendall + pente de Sen, verdict, mise en garde d'autocorrélation
- [x] Lien « Analyze as time series → » (désactivé tant que la page 012 n'existe pas)
- [x] Périodes incomplètes au début / à la fin : signalées, exclues du test (Sum, Count) — ajout constaté au navigateur
- [x] Table des données utilisées (période, valeur, moyenne, σ, n)
- [x] Tests : défauts, changement d'options, groupes, < 8 périodes

## Docs
- [x] `05-comparer.md`, `USER_GUIDE.md` (section Compare : vue temporelle, Mann-Kendall, pente de Sen)

## Vérification
- [x] Navigateur : `sales_timeseries` date × revenue (seul, puis par promo), période mois + fenêtre 6 centrée par l URL, clair et sombre ; semaines partielles signalées
