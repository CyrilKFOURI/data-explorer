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
| Date × number | Series (one point per day, week, month… ) | — |
| Date × category | Counts per period and category | — |

- **Color** splits a numeric pair or a series by a category. **Swap** exchanges X and Y.
- Each test shows its statistic, p-value, **effect size** with its magnitude (negligible, small, medium, large) and a sentence to read it. Statistics use every row; only the points drawn may be sampled (it is said under the chart).

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

Theme (system, light, dark), density, analysis defaults and detection thresholds, storage used by each dataset, version. See the Settings page for what each option does.

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

**Effect sizes** (Cohen's conventions) say whether a link matters in practice:

| Magnitude | r, ρ, τ, V | η | η², ε² | d |
|---|---|---|---|---|
| Small | ≥ 0.1 | ≥ 0.10 | ≥ 0.01 | ≥ 0.2 |
| Medium | ≥ 0.3 | ≥ 0.24 | ≥ 0.06 | ≥ 0.5 |
| Large | ≥ 0.5 | ≥ 0.37 | ≥ 0.14 | ≥ 0.8 |

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
