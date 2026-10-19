# User guide

Data Explorer is a local, offline tool to explore a table of data (CSV, Parquet or Excel) with real statistics: the right chart and the right test for each column, explained in plain words. Nothing leaves your machine, and your original file is never modified: the app works on its own copy.

## Quick start

1. **Home** → drop a file, choose one, or browse to a file or a folder (all files of a folder with the same columns are stacked into one dataset). Demo datasets are listed under *Samples*.
2. Check the import preview (separator, encoding, header row, decimal separator) and click **Import**.
3. Open **Columns** to check the type detected for each column, then **Validate types**.
4. Explore: **Overview** (every variable at a glance), a **variable page** (deep dive into one column), **Compare** (two or three variables), **Correlations** (every pair at once), **Data** (the rows themselves, and exports).
5. Press **F** at any time to filter the rows: the filter applies to every page.

## Pages

### Home

- The list of your datasets: rows, columns, size, last opened. Rename, re-import (instant when the source file hasn't changed) or delete a dataset from its menu.
- Import a **file** or a **folder**. Large files are converted once to Parquet; after that, every page reads the copy, which is fast even on millions of rows.

### Columns

Each column gets an **analysis type**, which decides which charts and statistical tests apply:

| Type | Meaning | Shown as |
|---|---|---|
| Continuous | A measured quantity (price, weight, duration) | Histogram, density, box plot; mean, quantiles, normality tests |
| Discrete | Few whole numbers (counts, ratings) | Bars per value |
| Category | Labels without order (country, product) | Top values, frequencies |
| Ordered category | Labels with an order (low < medium < high) | Bars in that order; edit the order with *Edit order* |
| Boolean | Two states (yes / no) | Two bars |
| Date / time | Moments in time | Volumes per period; date parts (year, month, weekday…) |
| Free text | Sentences | Lengths and frequent words |
| Identifier | One value per row (ids, emails) | Checked for duplicates only |
| Ignored | Empty, constant or not useful | Left out of analyses |

- **Detection** explains why a type was chosen ("100 % of values read as numbers"). Columns marked *Check* or *Unsure* deserve a look.
- **Change a type** from its badge. If some values can't be read in the new type, the app tells you how many become empty before you confirm.
- **Use** (checkbox) includes or excludes a column from every analysis. **Undo** (Ctrl+Z) reverts the last change; *Re-run detection* starts over (your manual corrections are kept).
- The **role** (amount, city, email…) is a finer hint used for display; it doesn't change the statistics.

### Overview

- **Summary strip**: rows (filtered / total), columns, missing values, duplicate rows and columns, size.
- **Alerts**: things worth a look — heavily skewed variables, high cardinality, constant or mostly empty columns, unreadable values.
- **One card per variable**, three per row: its chart and key numbers. Sort (file order, name, most missing, most distinct, most skewed), search, choose the *Top N* categories shown (the rest is grouped as *Others*) and the number of cards per page.
- On a card: **full screen** (every category, with a table of counts, % and cumulative %; for numbers, the full statistics and normality tests), **change the chart**, **download PNG**, **open the variable page**. Click a bar or a range to filter on it.

### Variable page

Everything about one column, in tabs. Use the arrows to go to the previous or next variable, and *Compare with…* to cross it with another one.

- **Summary** — counts (rows, missing, distinct), center and spread, quantiles, shape (see *Metrics* below). Charts: histogram (choose the number of bins), density, ECDF, box, violin, QQ-plot.
- **Normality** — five tests of "could these values come from a normal distribution?", with a verdict and the α level you choose.
- **Distribution** — candidate laws fitted to the data (normal, log-normal, exponential, gamma, Weibull…, Poisson for counts), ranked by AIC, drawn over the histogram; and transformations (log, square root, Box-Cox, Yeo-Johnson) previewed for symmetry. The data itself is never modified.
- **Outliers** — four rules to flag extreme values, the most extreme rows, and two buttons: *Show only these rows* / *Exclude them* (adds a filter).
- **Categories** (categories, booleans) — every value with count, %, cumulative %. **Dates** — range, granularity, rows per period, empty periods, rows per weekday and hour. **Text** — lengths and most frequent words. **Identifiers** — duplicates.

### Compare

Pick an **X** and a **Y**: the chart and the statistical tests follow their types.

| X × Y | Chart | Tests |
|---|---|---|
| Number × number | Scatter with linear fit (or density for many rows), 3D with a third number | Pearson r, Spearman ρ, Kendall τ |
| Number × category | Box, violin, or means ± 95 % CI per group | Welch t-test / Mann-Whitney (2 groups); ANOVA, Welch ANOVA, Kruskal-Wallis (3+ groups); Levene for equal spreads. The *Recommended* test is chosen from normality and spreads |
| Category × category | Heatmap of counts, or stacked 100 % bars | χ² test of independence, Fisher's exact test (2×2), Cramér's V |
| Date × number | Time series: one aggregated value per period, rolling mean and ± 1σ band | Mann-Kendall trend test, Sen's slope |
| Date × category | Counts per period and category | — |

- **Color** splits a numeric pair or a series by a category. **Swap** exchanges X and Y.
- **Time series** (date × number): rows are always **aggregated per period first** — a rolling mean over raw rows would mean nothing when a date has several rows. Above the chart, change:
  - **Period** — *Auto* uses the usual gap between dates, coarsened beyond 400 periods (3 years of daily data → weeks);
  - **Aggregate** — *Auto* sums amounts and quantities (by their column role) and averages everything else; also median, min, max, count;
  - **Window** of the rolling mean and standard deviation, in periods (*Auto*: 7 days, 4 weeks, 3 months…), **Trailing** (only looks back) or **Centered**;
  - which layers to draw: values, rolling mean, ± 1σ band (single series only).
  An empty period is a gap — except for sums and counts, where it is 0. A first or last period only partly covered by the data (a week starting mid-week) is drawn but left out of the trend test. *Data used* lists every period with its value, rolling mean, rolling σ and number of rows.
- Each test shows its statistic, p-value, **effect size** with its magnitude (negligible, small, medium, large) and a sentence to read it. Statistics use every row; only the points drawn may be sampled (it is said under the chart).

### Time series

*Modules › Time series* (needs a date column) analyses **one series** in depth. It opens already set up: the first date, the first amount or quantity column (otherwise the first number), and the automatic period and aggregate of *Compare*. *Analyze as time series →* in *Compare* opens it on the same choices.

- **Settings bar** (stays at the top): Time, Value, Period, Aggregate, **Group** (one series per category, up to 8; *Series* picks the one analysed), **Gaps** — leave empty periods empty, interpolate them, fill them with 0 or carry the last value forward. Methods that need a complete series interpolate on their own and say so.
- **Sections**, each opening on its conclusion (also shown in the side contents):
  - **Overview** — span, number of periods, empty periods, change between the first and last quarter; the curve with its rolling mean and ± 1σ band, a range slider to zoom, and *Show all series* to overlay the groups. Above the chart, **Rolling means** lists each mean with the colour of its curve; **+ Add** suggests windows that suit the period (4, 13, 26, 52 weeks…) or takes any number, up to five means; **Position** sets trailing or centered windows; **Show** turns the values, the means and the ± 1σ band (around the first mean) on or off.
  - **Seasonality** — boxes by weekday, month, quarter or hour (whichever the period allows), with the label furthest from the average once the trend is removed; one line per year to compare the latest year with the previous ones.
  - **Decomposition** — trend, seasonal and remainder, stacked on one time axis, with **STL** (robust, default), **MSTL** (several cycles, e.g. weekly and yearly), or **classical** additive / multiplicative moving averages. *Season length* overrides the cycle (7 days, 52 weeks, 12 months…). The **strengths** of trend and seasonality run from 0 (none) to 1 (dominant): above 0.64 is strong.
- **Methods**: every section lists the methods it ran; **+ Add method** offers every method that answers the same question, and your choice is remembered. Each method shows its conclusion, p-value, statistic, what it estimates, and *What it does* with its null hypothesis.

| Section | Methods (★ = shown by default) |
|---|---|
| Trend | ★ Mann-Kendall · ★ Sen's slope · Mann-Kendall corrected for autocorrelation (Hamed–Rao) · Seasonal Mann-Kendall · Cox–Stuart · Spearman ρ with time · Linear regression on time |
| Seasonality | ★ Kruskal–Wallis between seasons (ε²) · ★ Periodogram (dominant cycle length) · Friedman · QS test · Fisher's g · Autocorrelation at the seasonal lag |
| Stationarity | ★ ADF · ★ KPSS · ★ Phillips–Perron · DF-GLS · Zivot–Andrews (one break) · Variance ratio · Range unit-root |
| Autocorrelation | ★ Ljung–Box · ★ Durbin–Watson · Box–Pierce · Breusch–Godfrey · Runs test · Turning points · Bartels rank test |
| Volatility | ★ Breusch–Pagan · ★ ARCH-LM · White · Goldfeld–Quandt · McLeod–Li · Levene · Brown–Forsythe · Bartlett · Fligner–Killeen |
| Breaks | ★ Pettitt · CUSUM · Chow · Buishand range · SNHT |

- **Residuals** are what is left once trend and seasonality are removed (the STL remainder; a straight line's residuals when the series is too short for two cycles). With fewer than 7 cycles, the seasonal part is estimated as a plain average per position of the cycle, so it does not swallow the noise.
- **Volatility** — the residuals and their rolling standard deviation (type its window, e.g. 10), and tests of whether the variance changes over time or comes in clusters (ARCH). When the spread grows with the level, a log transformation is suggested.
- **Residuals** section — the full distribution, exactly as on a variable page: shape statistics (skewness, excess kurtosis), QQ-plot against a normal law, the normality tests, and the fitted laws ranked by AIC with transformations. Choose what to analyse: **Residuals**, the **Series** itself, or its **Returns** (relative change from one period to the next).
- **Breaks & anomalies** — change points found by **PELT** (exact) or **binary segmentation**, on the series without its seasonality. *Change in*: the **mean**, the **mean and variance**, or the **trend** (a straight line per segment: a change of slope). *Auto* uses the trend when the series has one, because cutting a steady trend into mean levels gives a staircase of false breaks. *Sensitivity* sets how strong a change must be. **Anomalies** are periods whose residual is unusual: robust z-score, IQR rule, rolling z-score, Hampel filter, the **generalized ESD test** (a formal test at α = 5 %, strict), **isolation forest** and **local outlier factor** (unusual windows of residuals) or a **masked autoencoder** (a small neural network rebuilds each period from its neighbours; periods it cannot rebuild break the pattern); threshold 3, 3.5 or 4 (not used by the ESD test). Every anomaly is marked on the chart; the table lists the 5 strongest, with **Show all** for the rest. Point anomalies are listed here; *contextual* ones (normal values at the wrong time of year) are caught because residuals have the season removed; *collective* ones (a lasting shift) are the breaks above; *Show rows* opens the Data page filtered on that period.
- An incomplete first or last period (a week that starts mid-week) is left out of every analysis when values are summed or counted: its total is too low.
- **Forecast** — runs when you click **Run forecast** (it fits each model several times). Choose the **horizon** (default: 30 days, 12 weeks, 12 months, 8 quarters… at most a quarter of the series) and the models: ★ **Naive**, ★ **Seasonal naive**, ★ **ETS (automatic)** (every exponential-smoothing form, lowest AICc), ★ **ARIMA (automatic)** (differences from the stationarity tests, then a stepwise search of the orders), plus Drift, Mean, Simple exponential smoothing, Holt, Holt-Winters, Theta, **SARIMA** with your own orders, **linear regression** on a trend and season indicators, and machine learning on the previous periods (**gradient boosting**, **neural network**; their intervals are approximate). Each model is scored on several **rolling origins**: it forecasts periods it has not seen, from several starting points. The table ranks the models by **MASE** (error relative to the naive reference: below 1 beats it) with MAE, RMSE, the gain over the reference, and the **coverage** of the 95 % interval (*All metrics* adds MAPE, sMAPE, RMSSE, bias, 80 % coverage and the Winkler interval score). The chart shows the history, the chosen model's forecast and its 80 % and 95 % intervals; click a model to draw it, *Show the other models* to overlay them, *Export CSV* to download the forecast. A Ljung–Box check says whether the model's residuals are white noise (the model captured the structure). You can cancel a running forecast.

- **Stationarity** — does the series keep a stable level and spread? ADF (H0: unit root) and KPSS (H0: stationary) ask opposite questions, so together they conclude: *stationary*, *not stationary*, *trend- or difference-stationary*, or *inconclusive*. Pick a **transformation** — log, difference, seasonal difference, log + difference, difference ×2, seasonal + difference — and the tests run on it; the simplest one that makes the series stationary is marked **Suggested**. With a strong trend, the tests are run around the trend.
- **Autocorrelation** — on the series as transformed above: the **ACF** (correlation with the value k periods earlier) and **PACF** (the same once shorter lags are accounted for; Yule-Walker, OLS or Burg), with the significance band ± 1.96/√n, and a reading of their shapes: slow decay → trend or unit root; spikes every cycle → seasonality; PACF stopping after lag p → an AR(p) model is a good start; nothing beyond chance → white noise. The **AR(p) model** is fitted with p chosen by AIC — or the order you pick — with its coefficients, the AIC / BIC of every order, and a Ljung–Box check of its residuals.

### Machine learning

*Modules › Machine learning* trains a model in one click. The only choice is **what to predict**: every column is listed with the problem it defines — a **number** (regression), **two classes** or **several classes** — or why it cannot be predicted (identifiers, free text, dates, mostly empty columns, categories with almost one value per row). Suggested targets come first.

- Choosing a target **trains a first model at once**: linear regression for a number, logistic regression for classes. Change its **essential settings** on the left (regularization: none, Ridge or Lasso and its strength; for classes, the strength C and *Balance classes*, on by default when the rarest class is under 20 %), then click **Train** again. Each training is kept in **Runs** (★ = best score): click one to see it again.
- **Preparation** is automatic and explained: each column gets decisions from named rules — left out (the target itself, identifiers, free text, constant or mostly empty columns, columns that *look like they contain the answer*, near-duplicates of another number), missing values filled (mean or median, plus a “was missing” indicator above 5 %), skewed numbers log-transformed or Yeo-Johnson, numbers standardised (robust scaling with many outliers), categories one-hot encoded (up to 15) or target-encoded, ordered categories coded in the order set in Columns, dates split into year, month, weekday… (month, weekday and hour as sine / cosine). Everything that learns from the data is fitted on the training rows only.
- **Model** opens a searchable list of every model, by family: linear models (OLS, ridge, lasso, elastic net, Huber, quantile, Bayesian, Poisson / Gamma / Tweedie, logistic, SGD…), discriminant analysis, nearest neighbours, support vector machines, Naive Bayes, trees, random forest and extra trees, boosting (histogram gradient boosting, gradient boosting, AdaBoost; XGBoost, LightGBM and CatBoost when installed), neural network (MLP), kernel ridge and Gaussian process. *Recommended for this data* comes first, with the reason. Models too slow for the data are greyed out with why.
- Under the model, its **essential settings**; **All settings** opens a side panel with every setting, grouped, each with why its default and its technical name. Turn on **Expert** for the optimizer (solver, learning rate, momentum, tolerance…). Options that cannot go together are greyed out with the reason (e.g. an L1 penalty needs the liblinear or saga solver).
- **Validation**: a train / test split (default 80 / 20), k-fold or repeated k-fold cross-validation, group k-fold (rows of one group never on both sides), a time-based split (test on the most recent rows) or leave-one-out; the primary metric; the seed; and how many rows to train on. With cross-validation, every row is predicted by a model that had not seen it, scores read *mean ± standard deviation* over the folds, and the saved model is retrained on every row. *All metrics* lists every metric of the problem.
- **Long trainings**: *How long will it take?* times the model on a sample and extrapolates; *Cancel* stops a training at its next step (nothing is saved). Iterative models (boosting, neural network) show their **learning curve**: training and held-out scores, iteration by iteration, with the one kept by early stopping. For two classes with a split, the **decision threshold** can be chosen on the training rows (best F1 or best balanced accuracy) instead of 0.5. Boosting models accept **monotonic constraints** (“size:+1, age:-1”): the prediction may only rise with size and only fall with age.
- **Compare models** trains a selection of models (one per suitable family by default) with their defaults on the same rows and validation, and ranks them; each becomes a run you can open. Tick two runs or more in **Runs** to see them side by side: every metric, the settings that differ, and the predictions (or ROC curves) overlaid. Only runs with the same target, classes and validation can be compared.
- **Tune** searches the best settings of the model within a budget (1, 5 or 15 minutes, or a number of trials), with 3-fold cross-validation on the training rows only: the test rows judge the result once, when you click **Use these settings**. You see the best score so far, the gain over the defaults and every trial live, and can stop at any time and keep the best. Expert: the search algorithm (TPE, random, grid, CMA-ES, NSGA-II), the early stop of bad trials, and the search space (bounds, log scale, fixed settings). After 20 trials or more, the settings that mattered most are shown.
- **Explain** shows why the model predicts what it predicts (computed once per run, then kept): what the model relies on (how much the score drops when each column is shuffled), how each column moves the predictions (SHAP values: exact for linear models, and for XGBoost / LightGBM when installed; other models say why they have none), the effect of one column on the average prediction (partial dependence, with how many rows sit at each value), and the tree itself for a decision tree. Columns so linked that their importance is shared are flagged. In **Predictions**, click a row to see how each column pushed its prediction up or down from the average.
- **Features** shows coefficients for linear models and the importance of each input for trees and boosting.
- **Predict as Classes** (number targets) cuts the number into ordered classes — *Low · Medium · High* — and trains a classification. Choose 2 to 10 classes and how to cut: *Equal counts* (same number of rows per class, the default), *Equal width* (same range; extremes beyond the 1st / 99th percentiles go to the end classes), *Natural breaks* (limits where the data has gaps) or *Custom* (drag the limits on the histogram, or move them with the arrow keys, Shift for bigger steps). *Round values* gives round limits (12,000 rather than 12,487.33). Rename a class by typing in its name. A class with too few rows is flagged with a one-click fix; a class with fewer than 5 rows cannot be trained. Training starts by itself 600 ms after your last change. Results add *Right or off by one*: the share of predictions in the right class or the next one. A count from 1 to 10 (a rating) can be predicted with one class per value.
- **Preparation · Edit** opens the preparation editor. *Automatic* applies the rules; change anything and it becomes *Custom* (*Reset all* goes back). The changes apply to the next training and are saved with its run (opening a run brings its choices back).
  - **Columns** — one row per column: use it or not, how missing values are filled (with an optional “was missing” flag), transform, encoding, scaling. Grey “Auto: …” values come from the rules (ⓘ shows which rule and why); your choices show a dot and a reset button. Choices a column or the model cannot take are greyed out with the reason (e.g. log needs every value ≥ 0; linear models need missing values filled). Left-out columns are listed last with their reason; most can be used anyway — a column that seems to contain the answer asks for confirmation.
  - **Selection** — optional statistical selection of the prepared inputs: low variance, correlated pairs, variance inflation (VIF), mutual information, univariate F test, L1 regularization, recursive elimination with cross-validation, permutation importance. Each has its threshold and shows how many inputs it kept; all are fitted on the training rows only.
  - **Missing & outliers** — the default for missing numbers (auto, mean, median, 0, KNN imputer, iterative imputer), the “was missing” threshold, rare categories, the one-hot limit, target-encoding smoothing, and outliers (left as they are by default; clip to the 1st–99th percentiles or to 1.5 IQR, or drop extreme training rows beyond 3 IQR — never test rows).
  - **Imbalance** (classes) — auto (class weights when the rarest class is under 20 %), none, class weights, random over- or under-sampling of the training rows, with the class counts before and after. The test rows keep the real shares.
  - **Preview** — the first 20 training rows exactly as the model receives them, with the name of every input (`city_Paris`, `signup_date_month_sin`…).
- **Validation**: 80 % of the rows to train, 20 % to test (stratified for classes), at most 200,000 training rows (a reproducible sample beyond).
- **Results** start with a sentence comparing the model with a naive reference — always predicting the average, or always answering the most frequent class — and say plainly when the model does no better.
  - *Regression*: R², MAE, RMSE (next to the average's), predicted against actual, residuals against predicted, residual distribution, and a Breusch–Pagan check of whether the error grows with the value.
  - *Classification*: accuracy (next to the majority class), balanced accuracy, macro F1, ROC AUC, log loss, the confusion matrix (counts or % of each actual class), precision / recall / F1 per class; for two classes, ROC, precision–recall and calibration curves and a **threshold** slider that updates the confusion matrix live.
  - *Features*: coefficients with 95 % interval, p-value and VIF (linear regression without penalty), the effect per unit of the original column, odds ratios for logistic regression.
  - *Predictions*: test rows with actual, predicted and error or probability; *Export CSV*.

### KPI

A business indicator in one click — revenue per month, distinct customers per week, average basket per quarter — as key figures, a chart and a table.

- **Suggested** KPIs open the page, read from your columns: *Rows*, *Total revenue* (amounts and quantities are summed), *Distinct customer_id* (identifiers that repeat), *Revenue per customer_id*, *% churned* (yes/no columns), *Average rating*. The first one is already computed; click another to see it.
- **Split by** chips under the chart add the best columns to split by (countries, regions, statuses first, then the columns with 3 to 12 values).
- **The builder** asks four questions: *Measure* (rows, or the sum, average, median, min, max, distinct count or % true of a column — up to 4 measures, plus a **ratio** of two, e.g. revenue ÷ distinct customers), *Over time* (date column, grain and period: all dates, the last N periods, year to date or a custom range; *Use the page filters* adds the filters to that period), *Split by* (one or two columns; beyond the 8 largest groups, the rest becomes *Other*). Changes take effect with **Calculate**.
- **Everything is chosen for you, with the reason**: the grain (the finest giving at most 60 periods), the chart (bars or areas for volumes that add up, lines for averages and shares, stacked bars per group, side-by-side bars for negative values or 3 periods or fewer, lines when one group makes over 70 % of the total, small multiples for two splits, horizontal bars or a heatmap without dates), the table layout (periods across up to 13 periods, in rows beyond), the number format. *Why this view* lists the choices.
- **Key figures**: the last complete period of each measure, its change against the previous period and the same period last year (arrows in neutral ink: a rise is not always good news), and a mini line of the last 24 periods. An incomplete period (the current month) is marked † and left out.
- **Totals are recomputed**: the total of an average, a median or a distinct count is computed on all the rows, never added up (a customer who bought in two countries counts once). *Other* is computed from its rows too.
- **Customize** changes any automatic choice — chart type, a *% of total* chart below, value labels, *Show as* (value, % of total / row / column, change vs previous, % change vs previous or last year, running total), table layout, totals, shading, compare columns, Top N, hiding *Other*, the order of the groups, and for each measure its name, decimals, compact numbers, prefix and suffix (€, km). Each setting says what Auto chose; options that would mislead are greyed out with the reason (stacking an average, a running total of a mean). A changed setting has a dot and *Reset to auto*. Display changes are instant: only the data changes recompute.
- **Table**: *Swap* rows and columns, sort by clicking a column, *Copy* (paste into a spreadsheet) or *Download CSV*.
- **Save** a KPI by name; saved KPIs are listed on the left (rename, duplicate, delete). The page's address keeps the KPI shown.

### Correlations

Every pair of variables measured at once, whatever their types.

- **Association matrix** (full width): blue = positive, red = negative (numeric pairs only); categories use Cramér's V and η, from 0 to 1. Choose *Pearson* or *Spearman* for numeric pairs, *Group related variables* (clustering) to put linked variables next to each other, and which columns to include (60 at most). Click a cell to open *Compare* on that pair. Above 200,000 rows, the matrix is computed on a reproducible sample of 200,000 rows.
- **Insights**: sentences grouped by theme — *Redundant variables*, *Relationships*, *Distributions*, *Data quality* — each with a **View** link to the chart that proves it.
- **Evidence level** of each link (badge with bars). *Show links* chooses what you see: *Strong*, *+ Moderate* (default) or *+ Weak*. Distribution and quality insights are always shown.
- **Focus on a variable**: what relates to it, best evidence first.
- **Strongest pairs**: table with measure, value, adjusted p-value, evidence and n.

### Data

The rows behind every chart, after your filters.

- **Scroll** through millions of rows (loaded 100 at a time). The first column is the row number in the file.
- **Rows to show**: *All rows*, *Random sample* (10,000 rows, always the same), *Duplicates* (identical rows, copies next to each other), *With missing values*.
- **Search** any column (case-insensitive). **Sort** by clicking a column name (ascending → descending → file order).
- Column menu (⋮): sort, *Filter on this column…*, *Pin to the left*, *Hide column*, *Open the variable page*. Hidden and pinned columns are remembered per dataset.
- Cells: numbers right-aligned, empty values as a grey "—", a value that can't be read in the column's type in orange italics (hover for details).
- **Export** what you see (filters, mode, search, sort) as **CSV**, **Parquet** or **Excel** (Excel holds 1,048,575 rows at most), with the visible columns or all of them; or the **column summary** (one row per column: type, missing, distinct, min, quartiles, max, mean, std, top value).

### Settings

- **Appearance**: theme (system, light, dark), density (compact, comfortable), animations (system, reduce, full).
- **Analysis defaults**: starting values of *Top categories per chart*, *Cards per page* and the normality tests' *α*, for datasets you haven't customised yet (each page can still change them). Remembered in this browser.
- **Type detection**: the thresholds used by the next detections (imports and *Re-run detection*): how many distinct whole numbers still count as *discrete* (20), the share of values that must read as numbers or dates to convert a text column (95 %), the share of distinct values that makes an *identifier* (95 %), the share of empty values that makes a column *ignored* (95 %). Validated types and manual corrections are kept. *Back to defaults* restores them.
- **Storage**: where the app keeps its copies (the workspace), the disk used in total and per dataset, and *Clear caches* to drop computed results kept in memory (rebuilt on demand).
- **About**: version and licence.
- The ↺ button next to a setting resets it to its default.

### Anywhere

- **Ctrl+K** (or the *Search or jump to…* button at the top) opens the command palette: type a few letters to go to a page, a variable of the open dataset or another dataset, or to run an action (open or clear the filters, change the theme, show the shortcuts). Arrows to move, Enter to run, Esc to close.
- **?** lists the keyboard shortcuts. **Guide** (bottom of the sidebar) opens this guide.

## Filters

Press **F** or click **Filter** (top right). Filters follow you on every page, live in the URL (shareable, reload-safe) and belong to one dataset.

- **AND between filters**, **OR between the values ticked** in one filter. Every condition has its opposite ("is none of", "outside", "is not empty"…). Empty values never pass a negated condition.
- Conditions by type: numbers (=, >, ≥, <, ≤, between, outside); categories (is any of, contains, starts with, equals); dates (before, after, between, falls on a weekday / month / quarter / hour); every type: is empty.
- **Unique values (one row each)** — keeps one row per value. *Based on*: **This column**, or **Several columns (key)** to tick the columns of a composite key (e.g. `vehicle_id` + `month`). *Keep*: the **first** or **last** row, in file order or **ordered by** a column (e.g. the latest date).
- **Duplicates only** — the rows whose value (or key) appears more than once, all copies. **Values appearing once** — the opposite: values present a single time (rows of duplicated values are removed entirely; to keep one row of each, use *Unique values*).
- Unique / duplicates conditions apply **after** the value conditions: *country = FR* + *unique vehicle_id (last)* gives the last French row of each vehicle.
- **Save** a set of filters under a name and apply it later. Click a chart (bar, range, outliers) to add a filter from it. Tick *Show active filters under the top bar* to keep them visible as chips.

## Metrics

### Describing one variable

| Metric | What it tells |
|---|---|
| Missing | Empty cells, plus null tokens like "N/A", "-", "null" |
| Unreadable | Values present in the file but impossible to read in the chosen type (e.g. "abc" in a number column); counted as missing in analyses |
| Distinct | Number of different values ("≈" when estimated, above 200,000 values) |
| Mean | The average; pulled by extreme values |
| Median | The middle value: half of the values are below. Robust to extremes |
| Std dev | Standard deviation: typical distance to the mean, in the variable's unit |
| CV | Coefficient of variation = std dev / mean: spread relative to the level (unitless) |
| MAD | Median absolute deviation: typical distance to the median, robust to outliers |
| Min, Q1, Q3, Max | Smallest value, 25 % quantile, 75 % quantile, largest value |
| IQR | Q3 − Q1: the range of the middle half of the values |
| P1, P5, P10, P90, P95, P99 | Values below which 1 %, 5 %, 10 %, 90 %, 95 %, 99 % of the data lie |
| Zeros, negatives, infinite | Counts of values equal to 0, below 0, or infinite (infinite values are left out of the statistics) |
| Sum | Total of the values |
| Skewness | Asymmetry: 0 = symmetric, > 0 = long tail to the right (a few very large values), < 0 = long tail to the left. Beyond ±1 it is clearly asymmetric; beyond ±2, strongly |
| Kurtosis | Tail weight compared with a normal distribution (excess kurtosis, normal = 0): > 0 = more extreme values than a normal, < 0 = fewer |

### Normality tests

Each test asks whether the values could come from a normal (bell-shaped) distribution. A **p-value below α** (0.05 by default) means "probably not normal".

| Test | How it works |
|---|---|
| Shapiro–Wilk | Compares the sorted values with those a normal would give. The most powerful general test for small and medium samples |
| D'Agostino–Pearson K² | Combines skewness and kurtosis: rejects data too asymmetric or with tails too heavy or too light |
| Anderson–Darling | Distance between the empirical and the normal distribution, with extra weight on the tails. Its p-value is bounded between 0.01 and 0.15, shown with "≤" or "≥" |
| Jarque–Bera | Checks that skewness and kurtosis match a normal's. Best with large samples |
| Lilliefors | Largest gap between the empirical distribution and a normal with the same mean and std dev (Kolmogorov–Smirnov corrected for estimated parameters) |

With thousands of rows, tests detect even tiny departures from normality: the **QQ-plot** tells whether they matter. Points on the line = normal; curving away at the ends = heavier or lighter tails.

### Fitting laws

| Metric | Meaning |
|---|---|
| AIC | Akaike information criterion: fit quality penalised by the number of parameters. Lower is better; only differences between laws matter (a gap above 10 is decisive) |
| BIC | Like AIC, with a stronger penalty on large samples |
| KS | Largest gap between the empirical and fitted distributions (0 = perfect) |
| λ (Box-Cox, Yeo-Johnson) | The power that makes the data most symmetric (λ = 0 ≈ log, 0.5 ≈ square root, 1 = unchanged) |

### Outlier rules

| Rule | Flags a value when |
|---|---|
| IQR × 1.5 | It is below Q1 − 1.5 × IQR or above Q3 + 1.5 × IQR (Tukey; the box plot's whiskers) |
| IQR × 3 | It is beyond 3 × IQR from the quartiles: only the most extreme values |
| z-score | It is more than 3 std devs from the mean. Assumes a roughly normal shape |
| Robust z | Its distance to the median, in MADs, is above 3.5 (Iglewicz & Hoaglin). Not fooled by the outliers themselves |

### Relationships between two variables

| Measure | Pair | Range | Reading |
|---|---|---|---|
| Pearson r | Number × number | −1 … 1 | Strength of a **linear** relationship; sign = direction |
| Spearman ρ | Number × number | −1 … 1 | Strength of a **monotonic** relationship (on ranks): robust to outliers and curves |
| Kendall τ | Number × number | −1 … 1 | Share of concordant minus discordant pairs; smaller values than ρ for the same strength |
| R² | Linear fit | 0 … 1 | Share of Y's variance explained by the line |
| η (correlation ratio) | Number × category | 0 … 1 | How much the number differs between groups; η² = share of variance explained by the groups |
| Cramér's V | Category × category | 0 … 1 | Strength of association (bias-corrected); 1 = one determines the other |
| Cohen's d | Number × 2 groups | 0 … ∞ | Difference of means, in pooled std devs |
| η² | Number × 3+ groups (ANOVA) | 0 … 1 | Share of the variance explained by the groups |
| ε² | Number × 3+ groups (Kruskal-Wallis) | 0 … 1 | Same idea, on ranks |
| Rank-biserial r | Mann-Whitney | −1 … 1 | How often one group's values exceed the other's |
| Mann-Kendall τ | Date × number | −1 … 1 | Over every pair of periods, how often the later value is higher; −1 = always falls, 1 = always rises |
| Sen's slope | Date × number | any | Median of the slopes between every pair of periods: the typical change per period, robust to outliers; with its 95 % interval and the change per year relative to the average level |

**Effect sizes** (Cohen's conventions) say whether a link matters in practice:

| Magnitude | r, ρ, τ, V | η | η², ε² | d |
|---|---|---|---|---|
| Small | ≥ 0.1 | ≥ 0.10 | ≥ 0.01 | ≥ 0.2 |
| Medium | ≥ 0.3 | ≥ 0.24 | ≥ 0.06 | ≥ 0.5 |
| Large | ≥ 0.5 | ≥ 0.37 | ≥ 0.14 | ≥ 0.8 |

The **Mann-Kendall test** runs on one value per period. When successive values are strongly linked (lag-1 autocorrelation above 0.5: a cycle or a slow drift), its p-value is optimistic, and the panel says so.

Cramér's V thresholds are lowered for tables with more than two rows and columns (Cohen's correction for the degrees of freedom).

### p-values and evidence

- A **p-value** is the probability of seeing a link at least this strong if there were none. Below 0.05 = *significant*: unlikely to be chance. It says nothing about the size of the link: with many rows, tiny effects become significant — look at the effect size.
- **Adjusted p-value** (*adj. p*, Benjamini-Hochberg): the Correlations page tests hundreds of pairs at once, and about 5 % of them would pass p < 0.05 by chance alone. The adjustment controls that share of false discoveries.
- **Evidence level** of a link crosses its effect size with its adjusted p-value:

| Level | Rule | Reading |
|---|---|---|
| Strong | Large effect and adj. p < 0.001 | A clear link, very unlikely to be chance |
| Moderate | At least medium effect and adj. p < 0.05 | A real link of notable size |
| Weak | Small effect with adj. p < 0.05, or notable effect with adj. p ≥ 0.05 | Real but minor, or possibly chance (the sentence says which) |
| None | Negligible effect, or small and not significant | No insight |

- **Redundant variables**: |r| or V above 0.95 — two columns carry almost the same information; keep one of them in models.

### Insights thresholds

| Insight | Rule |
|---|---|
| Skewed | \|skewness\| > 2 |
| Imbalanced | One category above 70 % of the rows |
| Missing | 20 % of the values or more |
| Relationship | Evidence level weak or above (see above) |
| Redundant | \|r\|, \|ρ\| or V > 0.95, significant |

## Keyboard shortcuts

| Keys | Action |
|---|---|
| F | Open the filters |
| Ctrl+K | Command palette: go to a page or a variable, run an action |
| ? | List the shortcuts |
| Ctrl+Z | Undo the last change on the Columns page |
| Esc | Close a panel, a menu or a dialog |

## Good to know

- **Large files**: every page works on millions of rows. Some heavy steps use a reproducible sample (always the same rows), and the page says so: points of a scatter, normality tests (5,000 values), law fitting (10,000 values), the correlation matrix (200,000 rows). Counts, means and test statistics use every row unless stated.
- **Types drive everything**: if a chart looks wrong, check the column's type on the Columns page first.
- **Privacy**: the app runs on your machine and never sends your data anywhere.
