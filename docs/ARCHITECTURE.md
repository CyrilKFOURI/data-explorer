# Architecture des dossiers

Objectif : pouvoir **ajouter une page, un module, un visuel, un test statistique ou un rôle de colonne sans toucher au reste**. Les dossiers marqués *(futur)* n'existent pas encore : ils montrent où les choses iront.

## Arborescence

```
New App/
├── CLAUDE.md · PLAN.md · .env.example · .gitignore
├── docs/                         ← voir CLAUDE.md pour l'index
├── samples/                      ← petits jeux de données de démo et de test (commités)
├── scripts/                      ← dev.ps1, build.ps1…
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
│   │   │   ├── ingestion/        ← readers/ (csv, parquet, excel), dossier, normalisation
│   │   │   ├── typing/           ← moteur de détection
│   │   │   │   ├── engine.py
│   │   │   │   ├── detectors/    ← un détecteur par fichier (dates, nombres, motifs, noms…)
│   │   │   │   └── knowledge_base/  ← *.yaml des rôles sémantiques
│   │   │   ├── profiling/        ← résumé du dataset, stats univariées
│   │   │   ├── stats/            ← tests statistiques, un fichier par famille + registry.py
│   │   │   │   ├── normality.py · distribution_fit.py · outliers.py
│   │   │   │   └── bivariate.py · correlations.py
│   │   │   ├── charts/           ← préparation des données des visuels (bins, KDE, Top N…)
│   │   │   ├── filters/          ← règles JSON → SQL DuckDB
│   │   │   └── insights/         ← règles qui rédigent les phrases d'insights
│   │   ├── api/                  ← routers HTTP fins : appellent domain/, ne calculent rien
│   │   │   └── datasets.py · columns.py · profile.py · charts.py · stats.py · filters.py
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
    │   ├── lib/                  ← formatage des nombres FR, utilitaires
    │   └── styles/               ← tokens.css, polices locales
    └── tests/e2e/
```

## Règles de dépendance

```
Frontend :  pages ─▶ features ─▶ charts ─▶ ui          modules ─▶ (features, charts, ui)
Backend  :  api ─▶ domain ─▶ core                       modules ─▶ (domain, core)
```

- `ui/` ne connaît rien du métier. `domain/` ne connaît rien de HTTP.
- **Un module n'importe jamais un autre module.** Ce qui doit être partagé descend dans `features/` ou `domain/`.
- Les pages n'appellent pas `fetch` directement : elles passent par `api/`.

## Recettes d'extension

| Je veux ajouter… | Je fais |
|---|---|
| Une page V1 | `frontend/src/pages/<nom>/` + une route dans `app/router.tsx` + `docs/pages/NN-nom.md` |
| Un module (ex. séries temporelles) | `backend/app/modules/<nom>/` (router, service, schemas) + l'enregistrer dans `modules/registry.py` ; `frontend/src/modules/<nom>/manifest.ts` (id, libellé, icône, routes, types de colonnes requis) + l'enregistrer dans `modules/registry.ts`. La barre latérale et les routes apparaissent seules. |
| Un visuel | `frontend/src/charts/builders/<visuel>.ts` (+ préparation dans `backend/app/domain/charts/` si besoin), voir [VISUALS.md](VISUALS.md) |
| Un test statistique | Une fonction dans `domain/stats/<famille>.py` enregistrée dans `stats/registry.py` (nom, types d'entrée, résultat + phrase d'explication). L'interface le liste automatiquement. |
| Un rôle de colonne | Une entrée YAML dans `domain/typing/knowledge_base/` + un cas de test, voir [COLUMN_DETECTION.md](COLUMN_DETECTION.md) |
| Une table SQLite | Une migration numérotée dans `core/migrations/` + mise à jour de [BACKEND_SCHEMA.md](BACKEND_SCHEMA.md) |
| Modifier une fonctionnalité existante | Mettre à jour d'abord sa doc (`docs/pages/…`), ensuite le code et les tests |
