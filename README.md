# Data Explorer

Local, offline exploratory data analysis with real statistical depth: normality tests, distribution fitting, bivariate tests with effect sizes and checked assumptions — every result explained, no code required.

> **Status:** early development (foundation in place, features coming sprint by sprint).

## Run it

Requires [Docker](https://www.docker.com/).

```bash
docker compose up --build
```

Then open <http://localhost:8000>. Put files you want to explore in `./data` (or set `DATA_DIR` in `.env`): they are mounted read-only.

## Develop

Requires [uv](https://docs.astral.sh/uv/) and Node 22.

```powershell
cd backend; uv sync; cd ..\frontend; npm install; cd ..
./scripts/dev.ps1
```

| Task | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Test | `uv run pytest` | `npm test` |
| Lint | `uv run ruff check .` | `npm run lint` |
| Typecheck | `uv run pyright` | `npm run typecheck` |

## Stack

FastAPI · SQLite · React + TypeScript + Vite · TanStack Router & Query · Tailwind CSS · Plotly (coming) · DuckDB & Polars (coming).

## License

[MIT](LICENSE)
