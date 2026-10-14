"""Chart data and tests for a pair (or triple) of columns, chosen from their analysis types."""

import math
from dataclasses import dataclass, field
from typing import Literal

import duckdb
import numpy as np
from scipy import stats as scipy_stats

from app.core.errors import AppError
from app.domain.compare.stats import (
    BivariateTest,
    GroupStats,
    contingency_tests,
    correlation_effect,
    group_tests,
    pearson,
    rank_correlations,
)
from app.domain.filters.scope import TypedColumn
from app.domain.ingestion.sql import lit
from app.domain.typing.dates import STEP_FORMATS, auto_step
from app.domain.typing.parsers import typed_sql
from app.domain.typing.types import AnalysisType, Parser
from app.domain.variable.source import SEED, clean

Role = Literal["num", "cat", "date"]
Kind = Literal["scatter", "groups", "contingency", "timeline", "date_counts"]

ROLES: dict[str, Role] = {
    "numeric_continuous": "num",
    "numeric_discrete": "num",
    "categorical_nominal": "cat",
    "categorical_ordinal": "cat",
    "boolean": "cat",
    "datetime": "date",
}
MAX_POINTS = 20_000
TEST_SAMPLE = 5_000
VIOLIN_SAMPLE = 1_000
MAX_GROUPS = 12
MAX_TABLE = 15
MAX_SERIES = 8
DENSITY_BINS = 40
OTHERS = "Others"


class NotComparableError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_comparable", status_code=422)


@dataclass
class CompareColumn:
    name: str
    type: AnalysisType
    parser: Parser
    order: list[str] | None = None

    @property
    def role(self) -> Role:
        role = ROLES.get(self.type)
        if role is None:
            raise NotComparableError(f"{self.name!r} ({self.type}) can't be compared.")
        return role


@dataclass
class Points:
    x: list[float]
    y: list[float]
    z: list[float] | None = None
    color: list[str] | None = None


@dataclass
class Regression:
    slope: float
    intercept: float
    r2: float | None


@dataclass
class Density:
    x_edges: list[float]
    y_edges: list[float]
    counts: list[list[int]]  # [y bin][x bin]


@dataclass
class Group:
    label: str
    n: int
    mean: float | None
    std: float | None
    q1: float | None
    median: float | None
    q3: float | None
    low: float | None  # whisker ends: Tukey fences clipped to the data range
    high: float | None
    ci_low: float | None  # 95% confidence interval of the mean
    ci_high: float | None
    sample: list[float] = field(default_factory=list)


@dataclass
class Contingency:
    rows: list[str]  # categories of Y
    columns: list[str]  # categories of X
    counts: list[list[int]]


@dataclass
class Series:
    label: str | None
    periods: list[str]
    values: list[float | None]
    low: list[float | None] = field(default_factory=list)
    high: list[float | None] = field(default_factory=list)


@dataclass
class Comparison:
    kind: Kind
    x: str
    y: str
    z: str | None
    color: str | None
    roles: dict[str, Role]
    rows: int  # rows where every chosen column has a value
    total: int  # rows after the global filters
    sample: int | None = None  # points drawn, when fewer than `rows`
    group_axis: Literal["x", "y"] | None = None
    points: Points | None = None
    regression: Regression | None = None
    density: Density | None = None
    groups: list[Group] = field(default_factory=list)
    contingency: Contingency | None = None
    series: list[Series] = field(default_factory=list)
    step: str | None = None
    tests: list[BivariateTest] = field(default_factory=list)
    message: str | None = None


def label_sql(column: TypedColumn) -> str:
    """Category label, as the charts and filters show it."""
    typed = typed_sql(column.name, column.parser)
    if column.type == "boolean":
        return f"(CASE WHEN {typed} THEN 'True' WHEN NOT {typed} THEN 'False' END)"
    return f"CAST({typed} AS VARCHAR)"


def number_sql(column: TypedColumn) -> str:
    return f"CAST({typed_sql(column.name, column.parser)} AS DOUBLE)"


class Comparer:
    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        source: str,
        x: CompareColumn,
        y: CompareColumn,
        z: CompareColumn | None = None,
        color: CompareColumn | None = None,
    ) -> None:
        self.connection = connection
        self.source = source
        self.x, self.y, self.z, self.color = x, y, z, color
        if x.name == y.name:
            raise NotComparableError("Pick two different columns.")
        if color is not None and color.role != "cat":
            raise NotComparableError(f"Color needs a category: {color.name!r} is {color.type}.")
        if z is not None and not (x.role == y.role == z.role == "num"):
            raise NotComparableError("A Z axis needs three numeric columns.")

    def one(self, sql: str) -> tuple:
        return self.connection.execute(sql).fetchone() or ()

    def all(self, sql: str) -> list[tuple]:
        return self.connection.execute(sql).fetchall()

    def value_sql(self, column: CompareColumn) -> str:
        role = column.role
        if role == "num":
            return number_sql(column)
        if role == "date":
            return f"CAST({typed_sql(column.name, column.parser)} AS TIMESTAMP)"
        return label_sql(column)

    def rows_of(self, columns: dict[str, CompareColumn]) -> str:
        """The rows where every given column has a usable value, as named columns."""
        selected = ", ".join(f"{self.value_sql(c)} AS {alias}" for alias, c in columns.items())
        conditions = " AND ".join(
            f"{alias} IS NOT NULL" + (f" AND isfinite({alias})" if c.role == "num" else "")
            for alias, c in columns.items()
        )
        return (
            f"(SELECT * FROM (SELECT {selected}, file_row_number AS rn FROM {self.source}) "
            f"WHERE {conditions})"
        )

    def total(self) -> int:
        return int(self.one(f"SELECT count(*) FROM {self.source}")[0])

    def sample(self, relation: str, columns: str, size: int) -> list[tuple]:
        return self.all(f"SELECT {columns} FROM {relation} ORDER BY hash(rn + {SEED}) LIMIT {size}")

    # --- Dispatch -----------------------------------------------------------------------------

    def compare(self) -> Comparison:
        roles: dict[str, Role] = {self.x.name: self.x.role, self.y.name: self.y.role}
        pair = (self.x.role, self.y.role)
        if pair == ("num", "num"):
            result = self.scatter()
        elif "date" in pair and "num" in pair:
            result = self.timeline()
        elif "date" in pair and "cat" in pair:
            result = self.date_counts()
        elif pair == ("cat", "cat"):
            result = self.contingency()
        elif "num" in pair and "cat" in pair:
            result = self.groups()
        else:
            raise NotComparableError(
                "Two dates can't be compared: pick a numeric or category column."
            )
        result.roles = roles
        if self.z:
            result.roles[self.z.name] = "num"
        if self.color:
            result.roles[self.color.name] = "cat"
        return result

    def base(self, kind: Kind, rows: int) -> Comparison:
        return Comparison(
            kind,
            self.x.name,
            self.y.name,
            self.z.name if self.z else None,
            self.color.name if self.color else None,
            {},
            rows,
            self.total(),
        )

    # --- num × num -------------------------------------------------------------------------------

    def scatter(self) -> Comparison:
        columns = {"x": self.x, "y": self.y}
        if self.z:
            columns["z"] = self.z
        if self.color:
            columns["c"] = self.color
        relation = self.rows_of(columns)
        n, r, slope, intercept, r2, x_low, x_high, y_low, y_high = self.one(
            f"SELECT count(*), corr(x, y), regr_slope(y, x), regr_intercept(y, x), regr_r2(y, x), "
            f"min(x), max(x), min(y), max(y) FROM {relation}"
        )
        result = self.base("scatter", int(n))
        if n < 3:
            result.message = "Fewer than 3 rows have both values."
            return result
        names = ", ".join(columns)
        drawn = self.sample(relation, names, MAX_POINTS)
        result.sample = len(drawn) if len(drawn) < n else None
        values = list(zip(*drawn, strict=True)) if drawn else [[] for _ in columns]
        by_alias = dict(zip(columns, values, strict=True))
        result.points = Points(
            [float(v) for v in by_alias["x"]],
            [float(v) for v in by_alias["y"]],
            [float(v) for v in by_alias["z"]] if "z" in by_alias else None,
            self.top_labels([str(v) for v in by_alias["c"]], MAX_SERIES)
            if "c" in by_alias
            else None,
        )
        if slope is not None and intercept is not None:
            result.regression = Regression(float(slope), float(intercept), clean(r2))
        result.density = self.density(relation, x_low, x_high, y_low, y_high)
        tested = self.sample(relation, "x, y", TEST_SAMPLE)
        xs = np.array([row[0] for row in tested], dtype=float)
        ys = np.array([row[1] for row in tested], dtype=float)
        result.tests = [pearson(clean(r), int(n)), *rank_correlations(xs, ys)]
        if result.tests[0].p_value is not None and r2 is not None:
            result.tests[
                0
            ].note = f"R² = {float(r2):.3f}: share of Y's variance a straight line explains."
        return result

    @staticmethod
    def top_labels(labels: list[str], limit: int) -> list[str]:
        """Keep the most frequent labels, the rest becomes "Others" (fixed palette order)."""
        counts: dict[str, int] = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        kept = set(sorted(counts, key=lambda label: (-counts[label], label))[:limit])
        return [label if label in kept else OTHERS for label in labels]

    def density(self, relation: str, x_low, x_high, y_low, y_high) -> Density | None:
        if None in (x_low, x_high, y_low, y_high) or x_low == x_high or y_low == y_high:
            return None
        bins = DENSITY_BINS
        x_width = (x_high - x_low) / bins
        y_width = (y_high - y_low) / bins
        rows = self.all(
            f"SELECT LEAST(CAST(floor((x - {x_low}) / {x_width}) AS INTEGER), {bins - 1}) AS i, "
            f"LEAST(CAST(floor((y - {y_low}) / {y_width}) AS INTEGER), {bins - 1}) AS j, count(*) "
            f"FROM {relation} GROUP BY i, j"
        )
        counts = [[0] * bins for _ in range(bins)]
        for i, j, count in rows:
            counts[int(j)][int(i)] = int(count)
        return Density(
            [x_low + k * x_width for k in range(bins + 1)],
            [y_low + k * y_width for k in range(bins + 1)],
            counts,
        )

    # --- num × cat -------------------------------------------------------------------------------

    def groups(self) -> Comparison:
        numeric, category = (self.x, self.y) if self.x.role == "num" else (self.y, self.x)
        relation = self.rows_of({"v": numeric, "g": category})
        (n,) = self.one(f"SELECT count(*) FROM {relation}")
        result = self.base("groups", int(n))
        result.group_axis = "x" if category is self.x else "y"
        if n < 3:
            result.message = "Fewer than 3 rows have both values."
            return result
        counted = self.all(f"SELECT g, count(*) AS c FROM {relation} GROUP BY g ORDER BY c DESC, g")
        kept = [str(label) for label, _ in counted[:MAX_GROUPS]]
        if category.type == "categorical_ordinal" and category.order:
            rank = {label: i for i, label in enumerate(category.order)}
            kept.sort(key=lambda label: rank.get(label, len(rank)))
        listed = ", ".join(lit(label) for label in kept)
        grouped = (
            f"(SELECT v, CASE WHEN g IN ({listed}) THEN g ELSE '{OTHERS}' END AS g, rn "
            f"FROM {relation})"
        )
        summaries = {
            str(label): row
            for label, *row in self.all(
                f"SELECT g, count(*), avg(v), var_samp(v), min(v), max(v), "
                f"quantile_cont(v, [0.25, 0.5, 0.75]) FROM {grouped} GROUP BY g"
            )
        }
        samples = {
            str(label): [float(v) for v in values]
            for label, values in self.all(
                f"SELECT g, list(v) FROM (SELECT g, v, row_number() OVER "
                f"(PARTITION BY g ORDER BY hash(rn + {SEED})) AS k FROM {grouped}) "
                f"WHERE k <= {max(VIOLIN_SAMPLE, TEST_SAMPLE // max(len(kept), 1))} GROUP BY g"
            )
        }
        order = kept + ([OTHERS] if OTHERS in summaries else [])
        result.groups = [
            self.group(label, summaries[label], samples.get(label, [])) for label in order
        ]
        tested = [g for g in result.groups if g.label != OTHERS]
        group_stats = [GroupStats(g.n, g.mean or 0.0, (g.std or 0.0) ** 2) for g in tested]
        group_samples = [np.array(g.sample, dtype=float) for g in tested]
        for group in result.groups:
            group.sample = group.sample[:VIOLIN_SAMPLE]
        result.tests = group_tests(group_stats, group_samples) if len(tested) >= 2 else []
        if len(counted) > MAX_GROUPS:
            result.message = (
                f'{len(counted) - MAX_GROUPS} smaller groups are shown together as "{OTHERS}" '
                "and left out of the tests."
            )
        return result

    @staticmethod
    def group(label: str, row: list, sample: list[float]) -> Group:
        count, mean, var, low, high, quartiles = row
        q1, median, q3 = (clean(v) for v in quartiles) if quartiles else (None, None, None)
        std = math.sqrt(var) if var is not None and var >= 0 else None
        whisker_low = whisker_high = None
        if q1 is not None and q3 is not None:
            spread = q3 - q1
            whisker_low = max(float(low), q1 - 1.5 * spread)
            whisker_high = min(float(high), q3 + 1.5 * spread)
        ci_low = ci_high = None
        if std is not None and count > 1:
            margin = float(scipy_stats.t.ppf(0.975, count - 1)) * std / math.sqrt(count)
            ci_low, ci_high = mean - margin, mean + margin
        return Group(
            label,
            int(count),
            clean(mean),
            clean(std),
            q1,
            median,
            q3,
            whisker_low,
            whisker_high,
            clean(ci_low),
            clean(ci_high),
            sample,
        )

    # --- cat × cat -------------------------------------------------------------------------------

    def contingency(self) -> Comparison:
        relation = self.rows_of({"a": self.x, "b": self.y})
        (n,) = self.one(f"SELECT count(*) FROM {relation}")
        result = self.base("contingency", int(n))
        if n < 3:
            result.message = "Fewer than 3 rows have both values."
            return result
        columns = self.kept_labels(relation, "a", self.x)
        rows = self.kept_labels(relation, "b", self.y)
        cells = self.all(
            f"SELECT {self.bucket('a', columns)} AS a, {self.bucket('b', rows)} AS b, count(*) "
            f"FROM {relation} GROUP BY 1, 2"
        )
        column_labels = columns + ([OTHERS] if any(c == OTHERS for c, _, _ in cells) else [])
        row_labels = rows + ([OTHERS] if any(r == OTHERS for _, r, _ in cells) else [])
        table = np.zeros((len(row_labels), len(column_labels)), dtype=int)
        for a, b, count in cells:
            table[row_labels.index(b)][column_labels.index(a)] = int(count)
        result.contingency = Contingency(row_labels, column_labels, table.tolist())
        result.tests = contingency_tests(table)
        return result

    def kept_labels(self, relation: str, alias: str, column: CompareColumn) -> list[str]:
        counted = self.all(
            f"SELECT {alias}, count(*) AS c FROM {relation} GROUP BY 1 ORDER BY c DESC, 1 "
            f"LIMIT {MAX_TABLE}"
        )
        labels = [str(label) for label, _ in counted]
        if column.type == "categorical_ordinal" and column.order:
            rank = {label: i for i, label in enumerate(column.order)}
            labels.sort(key=lambda label: rank.get(label, len(rank)))
        return labels

    @staticmethod
    def bucket(alias: str, kept: list[str]) -> str:
        listed = ", ".join(lit(label) for label in kept)
        return f"CASE WHEN {alias} IN ({listed}) THEN {alias} ELSE '{OTHERS}' END"

    # --- Dates -----------------------------------------------------------------------------------

    def date_and_other(self) -> tuple[CompareColumn, CompareColumn]:
        return (self.x, self.y) if self.x.role == "date" else (self.y, self.x)

    def step_for(self, relation: str) -> tuple[str, str]:
        span, timed = self.one(
            f"SELECT epoch(max(t)) - epoch(min(t)), "
            f"count(*) FILTER (WHERE t <> CAST(CAST(t AS DATE) AS TIMESTAMP)) FROM {relation}"
        )
        step = auto_step(float(span or 0), bool(timed))
        return step, STEP_FORMATS[step]

    def timeline(self) -> Comparison:
        date, numeric = self.date_and_other()
        columns = {"t": date, "v": numeric}
        if self.color:
            columns["c"] = self.color
        relation = self.rows_of(columns)
        (n,) = self.one(f"SELECT count(*) FROM {relation}")
        result = self.base("timeline", int(n))
        if n < 3:
            result.message = "Fewer than 3 rows have both values."
            return result
        step, fmt = self.step_for(relation)
        result.step = step
        group = "c" if self.color else "NULL"
        labels = None
        if self.color:
            labels = [
                str(v)
                for (v,) in self.all(
                    f"SELECT c FROM {relation} GROUP BY c "
                    f"ORDER BY count(*) DESC, c LIMIT {MAX_SERIES}"
                )
            ]
        rows = self.all(
            f"SELECT {group} AS g, strftime(date_trunc('{step}', t), '{fmt}') AS p, "
            f"avg(v), min(v), max(v) FROM {relation} "
            + (f"WHERE c IN ({', '.join(lit(label) for label in labels)}) " if labels else "")
            + f"GROUP BY g, date_trunc('{step}', t), p ORDER BY g, date_trunc('{step}', t)"
        )
        series: dict[str | None, Series] = {}
        for g, period, mean, low, high in rows:
            item = series.setdefault(g, Series(g, [], []))
            item.periods.append(str(period))
            item.values.append(clean(mean))
            item.low.append(clean(low))
            item.high.append(clean(high))
        result.series = [series[label] for label in (labels or [None]) if label in series]
        tested = self.sample(relation, "epoch(t), v", TEST_SAMPLE)
        times = np.array([row[0] for row in tested], dtype=float)
        values = np.array([row[1] for row in tested], dtype=float)
        trend = rank_correlations(times, values)[0]
        trend.note = "Monotonic trend over time (Spearman's ρ between date and value)."
        trend.effect = correlation_effect("rho", trend.statistic)
        result.tests = [trend]
        return result

    def date_counts(self) -> Comparison:
        date, category = self.date_and_other()
        relation = self.rows_of({"t": date, "c": category})
        (n,) = self.one(f"SELECT count(*) FROM {relation}")
        result = self.base("date_counts", int(n))
        if n < 3:
            result.message = "Fewer than 3 rows have both values."
            return result
        step, fmt = self.step_for(relation)
        result.step = step
        kept = [
            str(v)
            for (v,) in self.all(
                f"SELECT c FROM {relation} GROUP BY c ORDER BY count(*) DESC, c LIMIT {MAX_SERIES}"
            )
        ]
        rows = self.all(
            f"SELECT {self.bucket('c', kept)} AS g, "
            f"strftime(date_trunc('{step}', t), '{fmt}') AS p, "
            f"count(*) FROM {relation} GROUP BY g, date_trunc('{step}', t), p "
            f"ORDER BY date_trunc('{step}', t)"
        )
        periods = list(dict.fromkeys(str(p) for _, p, _ in rows))
        counts: dict[str, dict[str, int]] = {}
        for g, period, count in rows:
            counts.setdefault(str(g), {})[str(period)] = int(count)
        order = kept + ([OTHERS] if OTHERS in counts else [])
        result.series = [
            Series(label, periods, [float(counts[label].get(p, 0)) for p in periods])
            for label in order
            if label in counts
        ]
        return result


def compare(
    connection: duckdb.DuckDBPyConnection,
    source: str,
    x: CompareColumn,
    y: CompareColumn,
    z: CompareColumn | None = None,
    color: CompareColumn | None = None,
) -> Comparison:
    return Comparer(connection, source, x, y, z, color).compare()
