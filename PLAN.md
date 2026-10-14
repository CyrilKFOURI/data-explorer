# Plan

Roadmap en **sprints**, chacun composé de **tranches verticales** : chaque case = une feature complète (DB → API → UI), testable de bout en bout. Chaque feature a sa spec dans `docs/features/NNN-nom/` avant d'être codée.

## V1 — Explorateur

### Sprint 0 — Socle
- [ ] 000-socle (code fait ; reste : vérif Docker + revue design) — backend FastAPI + frontend React/Vite, une seule commande `dev`, healthcheck, SQLite + migrations, Shell (barre latérale, barre du haut, thème clair/sombre, tokens), routage, registres de modules vides, tests / lint / typecheck branchés, Dockerfile + docker-compose qui démarrent l'app, LICENSE MIT

### Sprint 1 — Données et types
- [x] 001-import — fichier ou dossier (CSV, Parquet, Excel) → aperçu → options → copie Parquet ; datasets récents ; réimport instantané si la source n'a pas changé ; upload + dossier monté `/data` ; jeux de démo dans `samples/`
- [x] 002-detection-types — moteur de règles + base de connaissances (TOML) + page Colonnes (revue, correction persistée, annulation) ; jeu de tests de détection

### Sprint 2 — Explorer
- [x] 003-vue-ensemble — bandeau de résumé + alertes qualité + grille 3 par ligne paginée ; règles d'affichage catégorielles (Top N, « Autres », plein écran)
- [x] 004-fiche-variable — stats complètes, tests de normalité, ajustement de lois, transformations, valeurs aberrantes, QQ-plot ; détails dans le plein écran de la Vue d'ensemble
- [x] 005-filtres — filtres globaux (bouton + panneau, ET entre filtres, OU entre valeurs), puces optionnelles, filtres enregistrés, filtrer depuis un graphique ou les outliers, sur toutes les pages

### Sprint 3 — Relations et sortie
- [x] 006-comparer — visuel et tests choisis selon les types (nuage + régression, densité, boîtes/violons/moyennes ± IC, heatmap, séries, 3D), tailles d'effet, couleur ; facettes et intention reportées
- [ ] 007-correlations-insights — matrice d'association mixte, clustering, paires classées, insights générés par règles
- [ ] 008-donnees-export — table virtualisée, modes d'affichage, exports CSV / Parquet / Excel / PNG
- [ ] 009-parametres-finitions — page Paramètres, palette de commandes, raccourcis, revue design et accessibilité
- [ ] 010-portfolio — README anglais avec captures, `docker compose up` testé sur une machine propre, image < 600 Mo, CI (tests + build Docker)

**→ Release V1.0**

## Modules (après la V1) — voir `docs/modules-futurs/`

- [ ] Sprint 4 — Module séries temporelles (stationnarité, hétéroscédasticité, décomposition, autocorrélation, prévision)
- [ ] Sprint 5 — Module machine learning (XGBoost par défaut, évaluation, SHAP, comparaison, Optuna)
- [ ] Sprint 6 — Module Builder KPI
- [ ] Sprint 7 — Module données synthétiques (CTGAN, TVAE/VAE, TimeGAN, évaluation de fidélité)
- [ ] À planifier — Module Assistant IA (LLM local optionnel)
- [ ] À planifier — Rapport HTML exportable du dataset
- [ ] À planifier — Vidéo / GIF de démo pour le README
- [ ] À planifier — Interface en français (i18n déjà prête)
