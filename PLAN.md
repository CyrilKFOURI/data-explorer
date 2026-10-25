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
- [x] 019-ml-catalogue-modeles — tous les modèles par familles, réglages à 3 niveaux (essentiels, avancés, expert / optimiseurs), validation — livré sans nouvelle dépendance (XGBoost / LightGBM / CatBoost déclarés, « Not installed in this build » en attendant l'accord) ; 019b livré (durée estimée, annulation, courbe d'apprentissage, contraintes monotones, seuil de décision, Radius neighbours, Categorical NB)
- [x] 020-ml-explicabilite — permutation importance, SHAP (natif boosting / forme close), dépendance partielle, explication par ligne — permutation, SHAP exact (linéaires) / natif (XGBoost, LightGBM si installés), dépendance partielle, arbre, waterfall d'une ligne, colonnes liées
- [x] 021-ml-comparaison-optimisation — comparer les modèles et les runs, optimisation Optuna (TPE, CMA-ES…) avec budget — Compare models, runs côte à côte, Tune (Optuna : TPE, aléatoire, grille, CMA-ES, NSGA-II ; élagage ; budget ; arrêt) ; xgboost, lightgbm, optuna, cmaes ajoutés

### Après
- [x] Sprint 6 — Module Builder KPI
  - [x] 022-kpi-builder — KPI suggérés depuis les colonnes, builder (mesures, ratio, temps, regroupements), choix automatiques par règles identifiées (grain, graphique, tableau, format) avec leur raison, Customize (Auto / reset, options interdites grisées), tableau croisé (totaux recalculés, Show as, export), KPI enregistrés
- [x] Sprint 7 — Module données synthétiques (page : `docs/pages/13-donnees-synthetiques.md`)
  - [x] 023-donnees-synthetiques — sans nouvelle dépendance : plan automatique par colonne (règles R-SYN), CART séquentiel / copule gaussienne / réseau bayésien Chow-Liu / colonnes indépendantes, rapport à la SDMetrics (Diagnostic, Quality, Detection, Privacy), comparaison colonne par colonne à la Sweetviz, liens, utilité TSTR / TRTR, confidentialité (copies, DCR, CAP), runs comparés, Save as dataset ; détection du GPU dans Paramètres
  - [x] 023b-modeles-profonds — CTGAN et TVAE codés d'après l'article (le paquet `ctgan` est sous BUSL), PyTorch CUDA en extra `deep`, entraînement sur le GPU avec repli CPU, époques automatiques, progression par époque
  - [x] 023c-timegan — TimeGAN codé d'après l'article : plan automatique des séquences (temps, entité, pas, longueur), fenêtres, historiques réels tenus à l'écart, entités et dates régénérées, onglet Sequences (autocorrélation, scores discriminant et prédictif)
- [x] 024-comparer-categories-couleur — nombres discrets (≤ 12 valeurs) lus comme catégories dans Compare (« As numbers » pour revenir), couleur sur les boîtes / violons / moyennes (au plus 15 boîtes et 5 couleurs, la catégorie la plus fournie passe sur l'axe)
- [x] Machine learning, mise en page des résultats (2026-10-20) — colonne de réglages collante avec la liste des runs, bande de métriques, graphiques Performance en grille de même hauteur (1 à 3 colonnes selon la largeur), Features en deux colonnes
- [x] Rapidité (2026-10-20) — `scripts/serve.ps1` (app compilée servie par le backend), plotly préchargé pendant les temps morts, graphiques dessinés un par un (ceux à l'écran d'abord, aucun n'attend le défilement)
- [x] 026-agent-ia — agent analyste par API (clé de l'utilisateur), module isolé ([spec](docs/features/026-agent-ia/spec.md))
  - [x] 026a — socle : moteur pur (boucle ReAct, budget, Stop, outils en parallèle, garde des effets de bord), fournisseur Anthropic (SDK en extra `[agent]`, flux, cache, réflexion adaptative, repli serveur), 7 outils en lecture seule sur les analyses V1, conversations en SQLite, flux SSE, panneau à droite (Ctrl+J) avec étapes et liens « Open in … », réglages et clé
  - [x] 026b — actions : contrat d'outil partagé (`core/tools.py`), point d'extension `Module.agent_tools` (chaque module déclare ses outils), 16 outils de plus, 23 en tout (ML : entraîner, comparer, optimiser, expliquer ; séries temporelles : analyser, prévoir ; KPI : suggérer, calculer, enregistrer ; synthétique : planifier, générer, enregistrer ; rapport HTML), confirmation avant toute écriture, progression des tâches longues
  - [x] 026b+ — tous fournisseurs (2026-10-22) : Claude par son SDK, tous les autres (Gemini, OpenAI, OpenRouter, Groq, Mistral, DeepSeek, serveur local) par le SDK `openai` au format chat-completions ; fournisseur reconnu à la forme de la clé, modèles lus depuis l'API, budget en tokens quand le prix est inconnu ; réglages : fournisseur, modèle, adresse d'un serveur local
  - [x] 026c — mémoire et qualité (2026-10-22) : vérificateur d'ancrage (chaque chiffre de la réponse cherché dans les résultats d'outils, les introuvables affichés sous la réponse), notes du dataset (table `agent_notes`, outil `remember` confirmé, vue Notes), six playbooks lus par `get_playbook`, compaction des anciens résultats, évaluation sur 15 cas dorés (`backend/evals/`) et ses corrections ; partage des lignes reporté en V2
- [x] 027-bibliotheque-python, phase 1 (2026-10-25) — le moteur devient le paquet `cyfouri-data-explorer` (`packages/`), dont l'app dépend : `dx.open()` / `from_pandas()`, types et corrections, vue d'ensemble, variable, lois, aberrants, compare, corrélations, filtres `where()`, lignes, export, rapport HTML, séries temporelles (prévisions comprises), KPI, ML (entraîner, comparer, optimiser, expliquer, prédire), synthétique ; `to_dict()` / `to_pandas()` ; test de parité app = bibliothèque, job CI du paquet seul, notebook d'exemple ([spec](docs/features/027-bibliotheque-python/spec.md))
  - [x] Phase 2 (2026-10-25) — les visuels de l'app en Python : `dx.plot(résultat)`, `ds.plot(colonne)`, figures portées depuis le frontend (plotly en extra `[plot]`), thème clair et sombre
  - [ ] Plus tard : `_repr_html_` dans Jupyter, l'app en extra `[app]`, publication sur PyPI (sur accord)
- [x] 025-rapport-html — rapport HTML autonome (sans script ni lien externe) : résumé et alertes, une fiche par variable avec graphique SVG, verdict de normalité et aberrants, matrice d'association, paires les plus liées et insights, manquants, méthodes ; sur les lignes filtrées ; tâche de fond avec progression et annulation ; bouton Export report (Vue d'ensemble) et menu Export (Données)
- [x] README pour GitHub (2026-10-22) : présentation, fonctionnalités par module, assistant, captures à jour de chaque page, architecture ; CONTRIBUTING
- [ ] À planifier — Vidéo / GIF de démo pour le README
- [ ] À planifier — Interface en français (i18n déjà prête)
- [ ] À planifier — Reconnaissance du thème du dataset : des « packs » par domaine (colonnes typiques et synonymes, indices sur les valeurs, KPI et visuels associés), reconnaissance par score sur les colonnes plutôt que le titre, suggestions transparentes (« reconnu grâce à… ») que l'utilisateur accepte ou corrige. Commencer par 3 packs bien faits (véhicules, ventes, RH) pour valider la méthode, puis l'étendre aux autres domaines une fois qu'elle est légère et fiable.
