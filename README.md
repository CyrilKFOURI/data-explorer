# Data Explorer

[![CI](https://github.com/CyrilKFOURI/data-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/CyrilKFOURI/data-explorer/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Exploratory data analysis with real statistical depth — local, offline, no code.**

Drop a CSV, Parquet or Excel file and get the right chart and the right test for every column: normality tests, distribution fitting, outlier rules, bivariate tests with effect sizes and checked assumptions, a mixed-type correlation matrix with multiple-testing correction — each result explained in plain words. Your data never leaves your machine.

![Overview of a dataset](docs/screenshots/overview.png)

## Why another EDA tool?

Automatic profilers give descriptive statistics and stop there. Doing a rigorous analysis still means writing a notebook for every new dataset. Data Explorer goes further:

- **The test follows the data.** Comparing a number across groups? It checks normality and equal spreads, then recommends Welch's t-test, ANOVA, Welch ANOVA, Mann-Whitney or Kruskal-Wallis — with the effect size and its magnitude, not just a p-value.
- **Honest about uncertainty.** Correlation insights cross the effect size with p-values adjusted for testing hundreds of pairs at once (Benjamini-Hochberg), and label each link *strong*, *moderate* or *weak*.
- **Types first.** A rule engine detects 9 analysis types (continuous, discrete, category, ordered, boolean, date, text, identifier, ignored), reads `"1 234,50 €"` as a number and `03/02/2024` as a date, and explains each decision. You can correct any of them.
- **Fast on real files.** DuckDB over a Parquet copy: millions of rows stay interactive; heavy steps use reproducible samples and say so.

## Features

| Page | What you get |
|---|---|
| **Columns** | Detected type and role for each column, with the reasons; change, exclude, undo |
| **Overview** | Summary, data quality alerts, one chart per variable; full screen with every category or the full statistics |
| **Variable** | Mean, quantiles, skewness, kurtosis; 5 normality tests and a QQ-plot; law fitting (AIC/BIC/KS) and Box-Cox / Yeo-Johnson previews; 4 outlier rules |
| **Compare** | Scatter + regression, box / violin / means ± CI, heatmaps, time series, 3D; Pearson, Spearman, Kendall, t-tests, ANOVA, χ², Fisher, Cramér's V… with effect sizes |
| **Correlations** | Association matrix for every pair (r / ρ, η, bias-corrected V), clustering, rule-based insights graded by evidence |
| **Data** | Virtualized table of millions of rows, search, sort, duplicates and missing-value views; export to CSV, Parquet or Excel |
| **Everywhere** | Global filters (AND / OR, unique values per key, duplicates only) on every page, command palette (Ctrl+K), light and dark themes |

| | |
|---|---|
| ![Variable page](docs/screenshots/variable.png) | ![Compare page](docs/screenshots/compare.png) |
| ![Correlations page](docs/screenshots/correlations.png) | ![Data page](docs/screenshots/data.png) |

The [user guide](docs/USER_GUIDE.md) — also available in the app — explains every page and every metric.

## Run it

Requires [Docker](https://www.docker.com/).

```bash
git clone https://github.com/CyrilKFOURI/data-explorer.git
cd data-explorer
docker compose up --build
```

Open <http://localhost:8000> and pick one of the demo datasets. To explore your own files, put them in `./data` (or set `DATA_DIR` in a `.env` file): the folder is mounted read-only and listed under *Browse*. You can also drop a file in the browser.

The app only listens on `127.0.0.1` and keeps its copies in a Docker volume (`workspace`).

## Develop

Requires [uv](https://docs.astral.sh/uv/) and Node 22.

```bash
cd backend && uv sync && cd ../frontend && npm install && cd ..
./scripts/dev.ps1   # backend on :8000, frontend on :5173
```

| Task | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Test | `uv run pytest` (add `-m slow` for the 5-million-row performance checks) | `npm test` |
| Lint | `uv run ruff check . && uv run ruff format --check .` | `npm run lint` |
| Typecheck | `uv run pyright` | `npm run typecheck` |

Statistics are tested against SciPy on reference data; performance checks run on 5 million rows.

## Architecture

- **Backend** — Python 3.12, FastAPI. Imports are converted once to Parquet; every analysis is a DuckDB query over that copy, with SciPy and NumPy for the statistics. SQLite stores datasets, column types, saved filters and settings.
- **Frontend** — React 19, TypeScript, Vite, TanStack Router & Query, Tailwind CSS on design tokens, Radix, Plotly. The API client is generated from the OpenAPI schema.
- **Distribution** — one Docker image serving the API and the built frontend.

More in [`docs/`](docs/) (product and technical notes, in French).

## License

[MIT](LICENSE)
