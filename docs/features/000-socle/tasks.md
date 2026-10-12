# 000 — Socle : tâches

## Backend
- [x] `backend/` initialisé avec `uv` (Python 3.12), `pyproject.toml`, ruff + pyright configurés
- [x] `app/config.py` : réglages via `.env` (workspace, port), `.env.example`
- [x] `app/core/storage.py` : création du workspace
- [x] `app/core/db.py` + `core/migrations/0001_init.sql` (tables `settings`, `schema_migrations`) + runner de migrations idempotent
- [x] `app/main.py` : app FastAPI, préfixe `/api/v1`, gestion d'erreurs (`core/errors.py`), service du front buildé en production
- [x] `api/health.py` : `GET /api/v1/health`
- [x] `modules/registry.py` + module de démonstration `hello`
- [x] Tests pytest : health, migrations (création + idempotence), registre de modules

## Frontend
- [x] `frontend/` Vite + React + TypeScript strict, ESLint, Vitest
- [x] Tailwind branché **uniquement** sur `styles/tokens.css` (palette par défaut désactivée), tokens clair/sombre + densité compacte
- [x] Polices IBM Plex Sans/Mono embarquées (paquets `@fontsource`, servies localement)
- [x] `app/` : router TanStack (`/`, `/settings`, 404), providers (Query, thème), Shell (Sidebar, TopBar)
- [x] Thème : suit le système, bascule mémorisée
- [x] `api/` : client typé généré depuis l'OpenAPI (script `gen:api`), hook `useHealth`
- [x] `modules/registry.ts` + manifeste `hello` → entrée de barre latérale + route
- [x] Page Accueil : état vide + indicateur de santé du backend
- [x] i18n : textes dans `lib/i18n/en.json` (anglais), aucun texte en dur dans les composants
- [x] Tests Vitest : registre de modules, thème, rendu du Shell

## Outillage
- [x] `scripts/dev.ps1` (backend + frontend en parallèle, proxy `/api`)
- [x] `Dockerfile` multi-étapes + `docker-compose.yml` (127.0.0.1:8000, volume workspace, `./data:/data:ro`)
- [x] `LICENSE` (MIT), `README.md` minimal (EN), `.gitignore` complété (node_modules, .venv, dist, data/)
- [x] Remplir la section Commandes de `CLAUDE.md`
- [x] Vérification : tests + lint + typecheck verts, build OK, UI vérifiée dans le navigateur (clair/sombre, réseau 100 % local)
- [ ] `docker compose up --build` vérifié (Docker Desktop arrêté ; téléchargement d'images à valider)
- [ ] Revue design avec les skills (`design-taste-frontend`, `impeccable`) sur le Shell
