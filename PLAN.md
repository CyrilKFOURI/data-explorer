# Plan

Roadmap en **sprints**, chacun composé de **tranches verticales** : chaque case = une feature complète (DB → API → UI), testable de bout en bout. Chaque feature a sa spec dans `docs/features/NNN-nom/` avant d'être codée.

## V1 — Explorateur

### Sprint 0 — Socle
- [x] 000-socle (Docker vérifié en 010, revue design et accessibilité en 009) — backend FastAPI + frontend React/Vite, une seule commande `dev`, healthcheck, SQLite + migrations, Shell (barre latérale, barre du haut, thème clair/sombre, tokens), routage, registres de modules vides, tests / lint / typecheck branchés, Dockerfile + docker-compose qui démarrent l'app, LICENSE MIT

### Sprint 1 — Données et types
- [x] 001-import — fichier ou dossier (CSV, Parquet, Excel) → aperçu → options → copie Parquet ; datasets récents ; réimport instantané si la source n'a pas changé ; upload + dossier monté `/data` ; jeux de démo dans `samples/`
- [x] 002-detection-types — moteur de règles + base de connaissances (TOML) + page Colonnes (revue, correction persistée, annulation) ; jeu de tests de détection

### Sprint 2 — Explorer
- [x] 003-vue-ensemble — bandeau de résumé + alertes qualité + grille 3 par ligne paginée ; règles d'affichage catégorielles (Top N, « Autres », plein écran)
- [x] 004-fiche-variable — stats complètes, tests de normalité, ajustement de lois, transformations, valeurs aberrantes, QQ-plot ; détails dans le plein écran de la Vue d'ensemble
- [x] 005-filtres — filtres globaux (bouton + panneau, ET entre filtres, OU entre valeurs), puces optionnelles, filtres enregistrés, filtrer depuis un graphique ou les outliers, sur toutes les pages

### Sprint 3 — Relations et sortie
- [x] 006-comparer — visuel et tests choisis selon les types (nuage + régression, densité, boîtes/violons/moyennes ± IC, heatmap, séries, 3D), tailles d'effet, couleur ; facettes et intention reportées
- [x] 007-correlations-insights — matrice d'association mixte (r/ρ, V corrigé, η), clustering, variable cible, paires classées, insights par règles masquables
- [x] 008-donnees-export — table virtualisée par blocs, modes (échantillon, doublons, manquants), recherche, tri, colonnes figées / masquées, exports CSV / Parquet / Excel + résumé (PNG déjà sur les cartes)
- [x] 009-parametres-finitions — guide utilisateur (docs/USER_GUIDE.md + page Guide), Paramètres (apparence, valeurs par défaut, seuils de détection, stockage, à propos), palette Ctrl+K, raccourcis `?`, revue accessibilité (contraste AA, skip link, color-scheme)
- [x] 010-portfolio — README anglais court avec captures, `docker compose up` testé, image 557 Mo, CI (tests, lint, typecheck, build Docker, test de fumée)

**→ Release V1.0** ✓

## Modules (après la V1) — voir `docs/modules-futurs/`

### Sprint 4 — Séries temporelles (page : `docs/pages/10-series-temporelles.md`, méthodes : `docs/TIMESERIES_METHODS.md`)
- [x] 011-vue-temporelle — Comparer date × num : agrégation par période, moyenne et écart-type glissants, Mann-Kendall + pente de Sen
- [x] 012-ts-page-visualisation — page `/timeseries` (module), configuration, vue d'ensemble, saisonnalité, décomposition STL
- [x] 013-ts-stationnarite-autocorrelation — ADF, KPSS, Phillips–Perron, différenciation suggérée, ACF/PACF, Ljung–Box, Durbin–Watson
- [x] 014-ts-volatilite-ruptures — hétéroscédasticité (BP, White, GQ, ARCH-LM, Levene), résidus, ruptures, anomalies
- [x] 015-ts-prevision — naïves, ETS, ARIMA auto, validation glissante, intervalles

### Sprint 5 — Machine learning (page : `docs/pages/11-machine-learning.md`)
- [x] 016-ml-premier-modele — page `/ml` (module), cible seule obligatoire, problème déduit, modèle linéaire / logistique entraîné aussitôt, résultats, runs
- [x] 017-ml-preparation-donnees — moteur de règles (type détecté × profil du modèle) : sélection, imputation, encodage, transformations, échelle, déséquilibre ; éditeur (choix par colonne et globaux, sélection statistique, aberrantes, aperçu)
- [x] 018-ml-cible-en-classes — cible numérique découpée en classes (nombre, méthode, aperçu en direct, noms, limites glissables, métriques « off by one »)
- [x] 019-ml-catalogue-modeles — tous les modèles par familles, réglages à 3 niveaux (essentiels, avancés, expert / optimiseurs), validation — livré sans nouvelle dépendance (XGBoost / LightGBM / CatBoost déclarés, « Not installed in this build » en attendant l'accord) ; reste 019b (durée estimée, annulation, courbe d'apprentissage, contraintes monotones, seuil de décision)
- [x] 020-ml-explicabilite — permutation importance, SHAP (natif boosting / forme close), dépendance partielle, explication par ligne — permutation, SHAP exact (linéaires) / natif (XGBoost, LightGBM si installés), dépendance partielle, arbre, waterfall d'une ligne, colonnes liées
- [x] 021-ml-comparaison-optimisation — comparer les modèles et les runs, optimisation Optuna (TPE, CMA-ES…) avec budget — Compare models, runs côte à côte, Tune (Optuna : TPE, aléatoire, grille, CMA-ES, NSGA-II ; élagage ; budget ; arrêt) ; xgboost, lightgbm, optuna, cmaes ajoutés

### Après
- [ ] Sprint 6 — Module Builder KPI
- [ ] Sprint 7 — Module données synthétiques (CTGAN, TVAE/VAE, TimeGAN, évaluation de fidélité)
- [ ] À planifier — Module Assistant IA (LLM local optionnel)
- [ ] À planifier — Rapport HTML exportable du dataset
- [ ] À planifier — Vidéo / GIF de démo pour le README
- [ ] À planifier — Interface en français (i18n déjà prête)
