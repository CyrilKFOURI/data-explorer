# cyfouri-data-explorer

The engine of [Data Explorer](https://github.com/CyrilKFOURI/data-explorer), for notebooks and scripts: column typing, profiles, the right test for every pair of variables, correlations with graded insights, time series, machine learning, KPIs, synthetic data and the HTML report. The same code computes the app's results, so the numbers match to the last digit.

```python
import cyfouri_data_explorer as dx

ds = dx.open("titanic.csv")
ds.types                       # detected types, roles and the reasons
ds.variable("Age")             # statistics, normality tests, outliers
ds.compare("Age", "Survived")  # the test follows the types, with an effect size
ds.correlations()              # mixed association matrix, ranked pairs, insights
ds.report("titanic.html")      # the app's report: one self-contained file
```

## Install

From the repository (not on PyPI yet):

```bash
pip install -e packages/cyfouri-data-explorer             # the core
pip install -e "packages/cyfouri-data-explorer[ml]"       # + XGBoost, LightGBM, Optuna
pip install -e "packages/cyfouri-data-explorer[deep]"     # + PyTorch: CTGAN, TVAE, TimeGAN
```

Python 3.12 or later. The core needs DuckDB, pyarrow, NumPy, SciPy, statsmodels, scikit-learn and pydantic; no server, no database.

## Open data

```python
ds = dx.open("sales.csv")                   # CSV, TSV, Parquet, Excel, or a folder of them
ds = dx.open("export.csv", delimiter=";", decimal=",", encoding="latin-1")
ds = dx.open("big.parquet", sample_pct=10)  # a reproducible 10 % sample
ds = dx.from_pandas(frame, "customers")     # or dx.from_arrow(table)
```

The CSV dialect is detected (separator, decimal comma, encoding). The source is copied once to Parquet in a cache folder (`~/.cache/cyfouri-data-explorer`, `%LOCALAPPDATA%` on Windows, or `CYFOURI_DATA_EXPLORER_CACHE`); opening an unchanged file again reuses the copy and the detected types.

## Types

Every column gets a type: `numeric_continuous`, `numeric_discrete`, `categorical_nominal`, `categorical_ordinal`, `boolean`, `datetime`, `text`, `identifier` or `ignored`. The type is read from a knowledge base of names and value checks: French decimals, `oui/non`, `21/02/2019`, `5%`, ZIP codes. Each detection says why it chose that type.

```python
ds.types                                    # every column (dx.to_pandas(ds.types) for a table)
ds.column("zip_code").reasons
ds.retype("Pclass", "categorical_ordinal")  # same rules as the app's Columns page
ds.set_order("size", ["S", "M", "L"])
ds.exclude("Name", "Ticket")                # out of the overview, correlations and report
ds.reset_types()
```

## Analyses

```python
ds.overview()                         # rows, types, missing cells, duplicates, quality alerts
ds.variable("Fare")                   # describe, normality (5 tests), KDE, ECDF, QQ
ds.fit("Fare")                        # probability laws ranked by AIC, transformations
ds.outliers("Fare", method="iqr")     # IQR, 3×IQR, z-score, robust z, and the rows
ds.compare("Fare", "Pclass")          # Welch / Mann-Whitney / ANOVA / Kruskal… + effect size
ds.compare("Age", "Fare", color="Sex")
ds.correlations(method="spearman")
ds.rows(limit=20, mode="duplicates")  # first, sample, duplicates, missing
ds.to_pandas()                        # every row, each column in its type
ds.export("clean.parquet")            # CSV, Parquet or Excel
```

## Filters

`where()` returns a filtered view and leaves `ds` alone. Conditions add up (AND); the values of `in` combine with OR. The operators are the app's filter bar: `eq`, `gt`, `gte`, `lt`, `lte`, `between`, `in`, `contains`, `starts_with`, `is_null`, `part_in`, `unique`, `duplicated`.

```python
women = ds.where("Sex", "in", ["female"])
adults = women.where("Age", "between", (18, 65))
adults.variable("Fare")
len(adults)
```

## Time series

```python
series = ds.timeseries(time="date", value="sales")  # period, aggregation, season: automatic
series.setup()                                      # the choices made, and why
series.overview()                                   # trend (Mann-Kendall, Sen's slope), rolling mean and spread
series.decomposition()                              # stl, mstl, classical_additive, classical_multiplicative
series.stationarity()                               # ADF, KPSS, Phillips-Perron and the suggested differencing
series.autocorrelation()                            # ACF, PACF, Ljung-Box, Durbin-Watson
series.volatility()
series.breaks()
series.residuals()
series.forecast(horizon=12)                         # naive models, ETS, ARIMA… ranked by MASE on rolling origins
```

## Machine learning

```python
ds.ml_targets()                         # every column as a target: regression, binary, multiclass
ml = ds.ml("Survived")
ml.preview()                            # the automatic preparation, column by column, and why
model = ml.train()                      # the app's first model: linear or logistic
model = ml.train("random_forest", settings={"n_estimators": 300})
model.score, model.scores               # held-out metrics
model.explain()                         # permutation importance, SHAP, partial dependence
model.predict(new_rows)                 # a Dataset or a pandas DataFrame
ml.compare()                            # one model per suitable family, best first
ml.tune("xgboost", budget_seconds=120)  # Optuna (the ml extra)
```

## KPIs

```python
suggested = ds.kpi_suggestions()
ds.kpi(suggested.kpis[0].definition)  # grain, totals and comparisons chosen by rules
```

## Synthetic data

```python
synth = ds.synthetic()
synth.plan()              # per column: model, regenerate, fake or leave out
made = synth.generate(
    method="cart", rows=10_000
)                         # also copula, bayes, independent, ctgan, tvae, timegan
made.report.scores        # diagnostic, quality, detection, privacy
made.utility("Survived")  # train on synthetic, test on real
made.to_dataset().compare("Age", "Fare")
made.save("synthetic.parquet")
```

## Results

Results are dataclasses, the same ones the app's API returns. Two helpers turn them into plain data:

```python
dx.to_dict(ds.variable("Age"))   # dicts and lists, JSON-ready (NaN → None)
dx.to_pandas(ds.correlations())  # the association matrix as a DataFrame
```

`to_pandas` knows rows, the association matrix, per-column statistics, laws, outliers, tests, targets, models, permutation importance, forecasts, KPI values, the synthetic plan and the types.

Every error is a `dx.ExplorerError` with a message you can act on. A mistyped column suggests the closest names:

```python
ds.variable("Agee")  # ColumnNotFound: Column 'Agee' not found; did you mean 'Age'?
```

## License

MIT
