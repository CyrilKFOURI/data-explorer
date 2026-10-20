# Data Explorer

[![CI](https://github.com/CyrilKFOURI/data-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/CyrilKFOURI/data-explorer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Explore a CSV, Parquet or Excel file with real statistics: the right chart and the right test for every column, explained in plain words. Local and offline.

![Overview](docs/screenshots/overview.png)

## Features

- **Column types** detected and explained (numbers, categories, dates, ids…), and editable.
- **Per variable**: statistics, normality tests, law fitting, outliers.
- **Compare** two variables: the chart and the test follow their types, with effect sizes.
- **Correlations** between every pair, with insights graded by evidence.
- **Data** table for millions of rows, global filters, exports to CSV, Parquet, Excel.

| | |
|---|---|
| ![Variable](docs/screenshots/variable.png) | ![Compare](docs/screenshots/compare.png) |
| ![Correlations](docs/screenshots/correlations.png) | ![Data](docs/screenshots/data.png) |

## Run

```bash
docker compose up --build
```

Open <http://localhost:8000> and pick a demo dataset. Put your own files in `./data` to browse them from the app.

## Develop

Requires [uv](https://docs.astral.sh/uv/) and Node 22: `./scripts/serve.ps1` builds the frontend and serves the whole app at http://127.0.0.1:8000 (`-Port 8001` if 8000 is taken), as fast as the Docker image. `./scripts/dev.ps1` starts the backend (FastAPI, DuckDB) and the frontend (React, Vite) with hot reload, to work on the code: much slower to use. Tests: `uv run pytest` in `backend/`, `npm test` in `frontend/`.

## Docs

- [User guide](docs/USER_GUIDE.md): every page and every metric (also in the app).
- [`docs/`](docs/): product and technical notes (in French).

## License

[MIT](LICENSE)
