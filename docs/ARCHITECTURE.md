# Architecture des dossiers

Objectif : pouvoir **ajouter une page, un module, un visuel, un test statistique ou un rôle de colonne sans toucher au reste**. Les dossiers marqués *(futur)* n'existent pas encore : ils montrent où les choses iront.

## Arborescence

```
New App/
├── CLAUDE.md · PLAN.md · README.md (EN) · LICENSE (MIT) · .env.example · .gitignore
├── Dockerfile                    ← multi-étapes : build du front (Node) → image Python slim
├── docker-compose.yml            ← port 127.0.0.1:8000, volume workspace, ./data monté en /data (lecture seule)
├── docker-compose.gpu.yml        (futur) variante CUDA pour ML / synthétique
├── docs/                         ← voir CLAUDE.md pour l'index
├── samples/                      ← démos commitées : titanic, iris, penguins, california_housing, typing_traps, série temporelle
├── scripts/                      ← dev.ps1, make_big_sample.py (≈5 M lignes, non commité)…
│
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py               ← crée l'app FastAPI, monte les routers, sert le front buildé
│   │   ├── config.py             ← réglages (.env) : workspace, seuils, limites
│   │   ├── core/                 ← transverse, sans logique métier
│   │   │   ├── db.py             ← SQLite (connexion, migrations dans core/migrations/)
│   │   │   ├── duck.py           ← connexion DuckDB, lecture des Parquet
│   │   │   ├── cache.py          ← cache des analyses (clés, LRU)
│   │   │   ├── storage.py        ← chemins du workspace
│   │   │   ├── jobs.py           ← tâches longues + progression
│   │   │   └── errors.py         ← erreurs métier → réponses HTTP claires
│   │   ├── domain/               ← LOGIQUE PURE : ni FastAPI ni HTTP, testable seule
│   │   │   ├── ingestion/        ← sources, détection CSV, lecture DuckDB, aperçu, import Parquet, navigation
│   │   │   ├── datasets/         ← dépôt SQLite + service (cycle de vie des datasets, jobs d'import)
│   │   │   ├── columns/          ← détections + corrections persistées, résumés par colonne
│   │   │   ├── typing/           ← moteur de détection
│   │   │   │   ├── engine.py
│   │   │   │   ├── detectors/    ← un détecteur par fichier (dates, nombres, motifs, noms…)
│   │   │   │   └── knowledge_base/  ← roles.toml, vocabulary.toml (rôles, valeurs nulles, booléens, ordres)
│   │   │   ├── profiling/        ← résumé du dataset, alertes qualité (Vue d'ensemble)
│   │   │   ├── stats/            ← tests statistiques, un fichier par famille + registry.py
│   │   │   │   ├── normality.py · distribution_fit.py · outliers.py
│   │   │   │   └── bivariate.py · correlations.py
│   │   │   ├── charts/           ← préparation des données des visuels (bins, Top N + Others, timeline, parties de date)
│   │   │   ├── filters/          ← règles JSON → SQL DuckDB
│   │   │   └── insights/         ← règles qui rédigent les phrases d'insights
│   │   ├── api/                  ← routers HTTP fins : appellent domain/, ne calculent rien
│   │   │   └── datasets.py · sources.py · jobs.py · errors.py (AppError → JSON) · (à venir : columns, profile, charts, stats, filters)
│   │   ├── schemas/              ← modèles Pydantic = contrats de l'API
│   │   └── modules/              ← modules optionnels, chacun autonome
│   │       ├── registry.py       ← liste des modules actifs → routers montés
│   │       ├── timeseries/       (futur) router.py · service.py · schemas.py · stats/
│   │       ├── ml/               (futur)
│   │       ├── kpi/              (futur)
│   │       ├── synthetic/        (futur)
│   │       └── assistant/        (futur)
│   └── tests/
│       ├── unit/                 ← miroir de domain/
│       ├── api/
│       └── fixtures/             ← datasets de test, dont typing/ (types attendus)
│
└── frontend/
    ├── package.json · vite.config.ts · tsconfig.json
    ├── src/
    │   ├── app/                  ← point d'entrée, router, providers (Query, thème), layout (Shell, Sidebar, TopBar)
    │   ├── pages/                ← une route = un dossier
    │   │   └── home/ · columns/ · overview/ · variable/ · compare/ · correlations/ · data/ · settings/
    │   ├── features/             ← blocs métier réutilisés par plusieurs pages
    │   │   └── filters/ · type-badge/ · summary-strip/ · chart-card/ · variable-grid/ · command-palette/
    │   ├── charts/               ← couche Plotly unique
    │   │   ├── Plot.tsx          ← wrapper (chargement paresseux, redimensionnement, thème)
    │   │   ├── theme.ts          ← tokens CSS → layout Plotly
    │   │   ├── rules/            ← règles d'affichage (Top N, orientation, échantillonnage)
    │   │   ├── builders/         ← un visuel par fichier
    │   │   └── registry.ts       ← types × intention → visuels possibles
    │   ├── modules/              ← pendant front des modules backend
    │   │   ├── registry.ts       ← manifestes → routes + entrées de la barre latérale
    │   │   └── timeseries/ (futur) manifest.ts · pages/ · components/
    │   ├── ui/                   ← design system : Button, Select, Dialog, Tooltip, Tabs, Table… (aucune logique métier)
    │   ├── api/                  ← client typé généré depuis l'OpenAPI du backend + hooks par ressource
    │   ├── stores/               ← état UI (filtres actifs, préférences)
    │   ├── lib/                  ← formatage des nombres (selon la locale), i18n, utilitaires
    │   └── styles/               ← tokens.css, polices locales
    └── tests/e2e/
```

## Règles de dépendance

```
Frontend :  pages ─▶ features ─▶ charts ─▶ ui          modules ─▶ (features, charts, ui)
Backend  :  api ─▶ domain ─▶ core                       modules ─▶ (domain, core)
```

- `ui/` ne connaît rien du métier. `domain/` ne connaît rien de HTTP.
- **Préparer la bibliothèque Python** ([modules-futurs/bibliotheque-python.md](modules-futurs/bibliotheque-python.md)) : un calcul de `domain/` prend des entrées simples (connexion DuckDB + relation, ou tableaux, + descriptions de colonnes) et rend des dataclasses ; il ne dépend ni de FastAPI, ni de SQLite, ni des services de l'app (la persistance reste dans les services et `modules/`).
- **Un module n'importe jamais un autre module.** Ce qui doit être partagé descend dans `features/` ou `domain/`.
- Les pages n'appellent pas `fetch` directement : elles passent par `api/`.

## Recettes d'extension

| Je veux ajouter… | Je fais |
|---|---|
| Une page V1 | `frontend/src/pages/<nom>/` + une route dans `app/router.tsx` + `docs/pages/NN-nom.md` |
| Un module (ex. séries temporelles) | `backend/app/modules/<nom>/` (router, service) + l'enregistrer dans `modules/registry.py` avec son `setup(app)` (crée ses services sur `app.state`) ; `frontend/src/modules/<nom>/manifest.ts` : `scope: "global"` (`/modules/<nom>`) ou `scope: "dataset"` (`/d/$datasetId/<nom>`, `requires` = types de colonnes nécessaires, grisé sinon), `validateSearch` optionnel, + l'enregistrer dans `modules/registry.ts`. La barre latérale et les routes apparaissent seules. Le calcul partagé avec une page V1 descend dans `domain/` (ex. `domain/timeseries/`, utilisé par Comparer et le module). |
| Un panneau à côté des pages (ex. l'assistant, 026) | Un composant qui décide lui-même quand s'afficher + un `PanelManifest` (`id`, `component`) listé dans `panels` de `frontend/src/modules/registry.ts` ; le Shell l'affiche à droite du contenu, sur toutes les pages. |
| Un module isolé avec son propre moteur (ex. l'agent, 026) | `backend/app/modules/agent/` : `engine/` pur (ni FastAPI, ni SQLite, ni SDK : testable avec un fournisseur simulé), `providers/` (SDK derrière l'interface `Provider`), `tools/` (chaque outil appelle les services V1 injectés via `AppServices`, jamais un autre module), `service.py` / `router.py` / `repository.py` autour. Le reste de l'app ne le connaît pas : une ligne dans `modules/registry.py`, une migration, un panneau. |
| Un outil de l'agent dans un module (026b) | `app/modules/<nom>/agent_tools.py` : des classes `Tool` (contrat partagé `app/core/tools.py` : entrée Pydantic, `kind` read / compute / write, sortie compacte + lien app, `wait_for` pour suivre une tâche de fond, `compact` pour alléger un résultat) et une fonction `agent_tools(app)`, déclarée dans `Module(agent_tools=…)` de `modules/registry.py`. Le module n'importe pas l'agent ; l'agent ramasse ces outils au démarrage. Un outil `write` est toujours confirmé par l'utilisateur. |
| Un visuel | `frontend/src/charts/builders/<visuel>.ts` (+ préparation dans `backend/app/domain/charts/` si besoin), voir [VISUALS.md](VISUALS.md) |
| Un test statistique | Une fonction dans `domain/stats/<famille>.py` enregistrée dans `stats/registry.py` (nom, types d'entrée, résultat + phrase d'explication). L'interface le liste automatiquement. |
| Un rôle de colonne | Une entrée TOML dans `domain/typing/knowledge_base/roles.toml` + un cas de test, voir [COLUMN_DETECTION.md](COLUMN_DETECTION.md) |
| Une table SQLite | Une migration numérotée dans `core/migrations/` + mise à jour de [BACKEND_SCHEMA.md](BACKEND_SCHEMA.md) |
| Modifier une fonctionnalité existante | Mettre à jour d'abord sa doc (`docs/pages/…`), ensuite le code et les tests |
