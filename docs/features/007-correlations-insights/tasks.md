# 007 — Corrélations & insights : tâches

## Backend
- [x] `domain/correlations/matrix.py` : colonnes éligibles, échantillon, Pearson / Spearman, V de Cramér corrigé, η, p-values, n par paire, clustering
- [x] `domain/correlations/insights.py` : règles, seuils, tri, identifiants stables, liens
- [x] API `GET /datasets/{id}/correlations?method&columns&filters`, cache
- [x] Tests : métriques vs calcul direct, clustering, insights, exclusions (dont catégories quasi uniques), filtres, perf 60 col × 5 M (slow, < 10 s : corrélations vectorisées, échantillon tiré sur le n° de ligne, insights sur les données chargées)

## Frontend
- [x] Route `/d/$datasetId/correlations`, entrée Correlations active
- [x] Matrice (palette divergente validée), méthode, clustering, choix des colonnes, clic → Compare
- [x] Variable cible : barres triées
- [x] Paires les plus fortes
- [x] Insights : liste, « View », masquer / réafficher
- [x] Tests : insights (liens, masquage mémorisé), matrice, paires, cible, méthode (64 tests frontend)

## Vérification
- [x] Navigateur : `typing_traps` (country/city redondants, price_eur asymétrique) et `sales_timeseries` (units ≈ revenue, différences par magasin, promo déséquilibrée), cible revenue
- [ ] Clic sur une case → Compare vérifié à l'œil (couvert par le code du clic Plotly déjà testé en 005)
