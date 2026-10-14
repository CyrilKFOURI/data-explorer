# 007 — Corrélations & insights : tâches

## Backend
- [x] `domain/correlations/matrix.py` : colonnes éligibles, échantillon, Pearson / Spearman, V de Cramér corrigé, η, p-values, n par paire, clustering
- [x] `domain/correlations/insights.py` : règles, seuils, tri, identifiants stables, liens
- [x] API `GET /datasets/{id}/correlations?method&columns&filters`, cache
- [x] Tests : métriques vs calcul direct, clustering, insights, exclusions (dont catégories quasi uniques), filtres, perf 60 col × 5 M (slow, < 10 s : corrélations vectorisées, échantillon tiré sur le n° de ligne, insights sur les données chargées)

## Frontend
- [x] Route `/d/$datasetId/correlations`, entrée Correlations active
- [x] Matrice (palette divergente validée), méthode, clustering, choix des colonnes, clic → Compare
- [x] Focus sur une variable (sous la matrice pleine largeur) : liste classée avec barre, mesure, lien Compare ; n.s. atténués
- [x] Paires les plus fortes : significatives d'abord, n.s. atténuées, variables colorées
- [x] Insights : regroupés par thème, noms de variables colorés par type, « View » ; masquage retiré (peu utile) ; liens entre variables seulement si p < 0,05
- [x] Tests : insights (liens, masquage mémorisé), matrice, paires, cible, méthode (64 tests frontend)

## Niveau de preuve (retour utilisateur : moins d'insights depuis le filtre p < 0,05)
- [x] `domain/correlations/evidence.py` : taille d'effet de Cohen, Benjamini-Hochberg, niveau ; porté par chaque paire (`q_value`, `evidence`)
- [x] Insights de lien selon le niveau, libellés adaptés, plafond par niveau ; tests (hasard → faible, réel → fort, petit → faible)
- [x] Front : sélecteur Show (mémorisé, comptes), pastilles sur insights, paires et focus ; tests
- [x] Docs, client typé, vérification navigateur (`sales_timeseries` : 3 forts, 2 faibles ; `typing_traps` : 1 fort, 1 faible)

## Vérification
- [x] Navigateur : `typing_traps` (country/city redondants, price_eur asymétrique) et `sales_timeseries` (units ≈ revenue, différences par magasin, promo déséquilibrée), cible revenue
- [ ] Clic sur une case → Compare vérifié à l'œil (couvert par le code du clic Plotly déjà testé en 005)
