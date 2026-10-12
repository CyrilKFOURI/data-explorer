# 000 — Socle : tâches

## Backend
- [ ] `backend/` initialisé avec `uv` (Python 3.12), `pyproject.toml`, ruff + pyright configurés
- [ ] `app/config.py` : réglages via `.env` (workspace, port), `.env.example`
- [ ] `app/core/storage.py` : création du workspace
- [ ] `app/core/db.py` + `core/migrations/0001_init.sql` (tables `settings`, `schema_migrations`) + runner de migrations idempotent
- [ ] `app/main.py` : app FastAPI, préfixe `/api/v1`, gestion d'erreurs (`core/errors.py`), service du front buildé en production
- [ ] `api/health.py` : `GET /api/v1/health`
- [ ] `modules/registry.py` + module de démonstration `hello`
- [ ] Tests pytest : health, migrations (création + idempotence), registre de modules

## Frontend
- [ ] `frontend/` Vite + React + TypeScript strict, ESLint, Vitest
- [ ] Tailwind branché **uniquement** sur `styles/tokens.css` (palette par défaut désactivée), tokens clair/sombre + densité compacte
- [ ] Polices IBM Plex Sans/Mono embarquées (`styles/fonts/`)
- [ ] `app/` : router TanStack (`/`, `/settings`, 404), providers (Query, thème), Shell (Sidebar, TopBar)
- [ ] Thème : suit le système, bascule mémorisée
- [ ] `api/` : client typé généré depuis l'OpenAPI (script `gen:api`), hook `useHealth`
- [ ] `modules/registry.ts` + manifeste `hello` → entrée de barre latérale + route
- [ ] Page Accueil : état vide + indicateur de santé du backend
- [ ] i18n : textes dans `lib/i18n/en.json` (anglais), aucun texte en dur dans les composants
- [ ] Tests Vitest : registre de modules, thème, rendu du Shell

## Outillage
- [ ] `scripts/dev.ps1` (backend + frontend en parallèle, proxy `/api`)
- [ ] `Dockerfile` multi-étapes + `docker-compose.yml` (127.0.0.1:8000, volume workspace, `./data:/data:ro`)
- [ ] `LICENSE` (MIT), `README.md` minimal (EN), `.gitignore` complété (node_modules, .venv, dist, data/)
- [ ] Remplir la section Commandes de `CLAUDE.md`
- [ ] Vérification finale : tests + lint + typecheck verts, `docker compose up --build` OK, revue design avec les skills ; cocher 000 dans `PLAN.md`
