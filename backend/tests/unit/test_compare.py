from datetime import datetime, timedelta
from typing import Any

import duckdb
import numpy as np
import pyarrow as pa
import pytest
from scipy import stats

from app.domain.compare.analyze import CompareColumn, NotComparableError, compare
from app.domain.compare.stats import GroupStats, anovas
from app.domain.typing.types import Parser

RAW = Parser(kind="raw")
N = 3_000


@pytest.fixture(scope="module")
def connection() -> duckdb.DuckDBPyConnection:
    rng = np.random.default_rng(3)
    groups = rng.choice(["a", "b", "c"], size=N, p=[0.5, 0.3, 0.2])
    shift = {"a": 0.0, "b": 1.0, "c": 3.0}
    spread = {"a": 1.0, "b": 1.0, "c": 4.0}
    x = rng.normal(0, 1, N)
    table = pa.table(
        {
            "file_row_number": pa.array(range(N)),
            "x": x,
            "y": 2 * x + rng.normal(0, 1, N),
            "z": rng.normal(0, 1, N),
            "g": groups,
            "two": np.where(groups == "a", "a", "other"),
            "v": [rng.normal(shift[g], spread[g]) for g in groups],
            "h": rng.choice(["u", "w"], size=N),
            "flag": rng.random(N) < 0.3,
            "when": [datetime(2024, 1, 1) + timedelta(days=int(i % 90)) for i in range(N)],
        }
    )
    con = duckdb.connect()
    con.register("t", table)
    con.execute("CREATE TABLE data AS SELECT * FROM t")
    return con


def col(name: str, kind: str) -> CompareColumn:
    return CompareColumn(name, kind, RAW)  # type: ignore[arg-type]


NUM, CAT, BOOL, DATE = "numeric_continuous", "categorical_nominal", "boolean", "datetime"


def frame(con: duckdb.DuckDBPyConnection, sql: str) -> dict[str, np.ndarray]:
    rows = con.execute(sql).fetchnumpy()
    return {key: np.asarray(value) for key, value in rows.items()}


def test_numeric_pair_matches_scipy(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("x", NUM), col("y", NUM))
    data = frame(connection, "SELECT x, y FROM data")

    pearson = next(t for t in result.tests if t.key == "pearson")
    expected: Any = stats.pearsonr(data["x"], data["y"])
    assert result.kind == "scatter" and result.rows == N
    assert pearson.statistic == pytest.approx(expected.statistic, rel=1e-9)
    assert pearson.p_value == pytest.approx(expected.pvalue, abs=1e-12)
    assert pearson.effect is not None and pearson.effect.magnitude == "large"
    slope: Any = stats.linregress(data["x"], data["y"])
    assert result.regression is not None
    assert result.regression.slope == pytest.approx(slope.slope, rel=1e-9)
    assert result.points is not None and len(result.points.x) == N
    assert result.density is not None and sum(map(sum, result.density.counts)) == N
    spearman = next(t for t in result.tests if t.key == "spearman")
    rho: Any = stats.spearmanr(data["x"], data["y"])
    assert spearman.statistic == pytest.approx(rho.statistic)


def test_two_groups_welch_and_cohen_d(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("two", CAT), col("v", NUM))
    data = frame(connection, "SELECT two, v FROM data")
    a, b = data["v"][data["two"] == "a"], data["v"][data["two"] == "other"]

    welch = next(t for t in result.tests if t.key == "welch_t")
    expected: Any = stats.ttest_ind(a, b, equal_var=False)
    assert result.kind == "groups" and result.group_axis == "x"
    assert welch.statistic == pytest.approx(expected.statistic, rel=1e-9)
    assert welch.p_value == pytest.approx(expected.pvalue, rel=1e-6, abs=1e-300)
    assert welch.recommended and welch.effect is not None and welch.effect.name == "d"
    assert [g.label for g in result.groups] == ["a", "other"]


def test_several_groups_anova_and_levene(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("v", NUM), col("g", CAT))
    data = frame(connection, "SELECT g, v FROM data")
    samples = [data["v"][data["g"] == label] for label in ("a", "b", "c")]

    by_key = {t.key: t for t in result.tests}
    f_test: Any = stats.f_oneway(*samples)
    kruskal: Any = stats.kruskal(*samples)
    assert by_key["anova"].statistic == pytest.approx(f_test.statistic, rel=1e-9)
    assert by_key["levene"].p_value is not None and by_key["levene"].p_value < 0.05
    assert by_key["welch_anova"].recommended and not by_key["anova"].recommended
    assert by_key["kruskal"].statistic == pytest.approx(kruskal.statistic, rel=1e-9)
    assert result.group_axis == "y"
    c = next(g for g in result.groups if g.label == "c")
    assert c.ci_low is not None and c.ci_low < (c.mean or 0) < (c.ci_high or 0)


def test_welch_anova_matches_reference() -> None:
    # Classic ANOVA must equal scipy exactly; Welch's ANOVA has no scipy twin, so it is checked
    # against Alexander-Govern, another heteroscedastic test of the same null hypothesis.
    groups = [GroupStats(10, 5.0, 1.0), GroupStats(12, 6.0, 4.0), GroupStats(8, 8.0, 9.0)]
    rng = np.random.default_rng(0)
    samples = [rng.normal(g.mean, np.sqrt(g.var), g.n) for g in groups]
    exact = [GroupStats(len(s), float(s.mean()), float(s.var(ddof=1))) for s in samples]

    classic, welch = anovas(exact)

    f_test: Any = stats.f_oneway(*samples)
    welch_reference: Any = stats.alexandergovern(*samples)
    assert classic.statistic == pytest.approx(
        f_test.statistic, rel=1e-9
    )  # same null; F from Welch's formula
    assert welch.p_value is not None and abs(welch.p_value - welch_reference.pvalue) < 0.05


def test_categories_chi2_and_cramers_v(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("g", CAT), col("flag", BOOL))
    data = frame(connection, "SELECT g, flag FROM data")

    observed = np.array(
        [
            [np.sum((data["g"] == g) & (data["flag"] == f)) for g in ("a", "b", "c")]
            for f in (False, True)
        ]
    )
    expected: Any = stats.chi2_contingency(observed, correction=False)
    chi2 = next(t for t in result.tests if t.key == "chi2")
    assert result.kind == "contingency" and result.contingency is not None
    assert sum(map(sum, result.contingency.counts)) == N
    assert chi2.statistic == pytest.approx(expected.statistic, rel=1e-9)
    assert chi2.effect is not None and chi2.effect.name == "V"


def test_two_by_two_offers_fisher(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("h", CAT), col("flag", BOOL))

    assert {t.key for t in result.tests} == {"chi2", "fisher"}


def test_date_and_number_timeline(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("when", DATE), col("v", NUM), color=col("two", CAT))

    assert result.kind == "timeline" and result.step == "day"
    assert {s.label for s in result.series} == {"a", "other"}
    assert result.tests[0].key == "spearman"


def test_date_and_category_counts(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("g", CAT), col("when", DATE))

    assert result.kind == "date_counts"
    assert sum(sum(v or 0 for v in s.values) for s in result.series) == N


def test_three_numbers_give_3d_points(connection: duckdb.DuckDBPyConnection) -> None:
    result = compare(connection, "data", col("x", NUM), col("y", NUM), col("z", NUM), col("g", CAT))

    assert result.points is not None and result.points.z is not None and result.points.color
    assert set(result.points.color) == {"a", "b", "c"}


def test_points_are_sampled_beyond_the_limit(connection: duckdb.DuckDBPyConnection) -> None:
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE big AS SELECT range AS file_row_number, random() AS x, random() AS y "
        "FROM range(30000)"
    )

    result = compare(con, "big", col("x", NUM), col("y", NUM))

    assert result.sample == 20_000 and result.rows == 30_000


@pytest.mark.parametrize(
    ("x", "y", "z", "color", "message"),
    [
        (col("x", NUM), col("x", NUM), None, None, "two different"),
        (col("x", NUM), col("y", NUM), col("g", CAT), None, "three numeric"),
        (col("x", NUM), col("y", NUM), None, col("z", NUM), "Color needs a category"),
        (col("x", NUM), col("y", "text"), None, None, "can't be compared"),
        (col("when", DATE), col("when2", DATE), None, None, "Two dates"),
    ],
)
def test_invalid_choices(connection, x, y, z, color, message) -> None:
    with pytest.raises(NotComparableError, match=message):
        compare(connection, "data", x, y, z, color)
