"""Summary of a whole dataset and its quality alerts (Overview page)."""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal

import duckdb

from app.domain.columns.service import ColumnView
from app.domain.ingestion.sql import ident, lit
from app.domain.typing.parsers import typed_sql

SKEW_ALERT = 2.0
HIGH_CARDINALITY = 0.5


@dataclass
class Alert:
    kind: str
    severity: Literal["warning", "info"]
    message: str
    columns: list[str] = field(default_factory=list)


@dataclass
class ColumnStats:
    missing_pct: float
    distinct: int
    skewness: float | None = None


@dataclass
class Overview:
    rows: int
    columns: int
    used_columns: int
    missing_cells: int
    missing_pct: float
    duplicate_rows: int
    duplicate_columns: list[list[str]]
    size_bytes: int
    types: dict[str, int]
    alerts: list[Alert]
    column_stats: dict[str, ColumnStats]


def plural(count: int, word: str, many: str | None = None) -> str:
    return f"{count} {word if count == 1 else (many or word + 's')}"


def _pct(part: float, whole: float) -> float:
    return round(100 * part / whole, 2) if whole else 0.0


def duplicate_rows(connection: duckdb.DuckDBPyConnection, source: str) -> int:
    total, unique = connection.execute(
        f"SELECT (SELECT count(*) FROM {source}), "
        f"(SELECT count(*) FROM (SELECT DISTINCT * FROM {source}))"
    ).fetchone() or (0, 0)
    return int(total - unique)


def duplicate_columns(
    connection: duckdb.DuckDBPyConnection, storage_path: str, names: list[str]
) -> list[list[str]]:
    """Groups of columns with identical content (compared as text, row by row)."""
    if len(names) < 2:
        return []
    # One hash per "row number + value" string, summed. (XOR-ing hashes is wrong: values that
    # repeat an even number of times cancel out, making unrelated columns look identical.)
    hashes = ", ".join(
        f"sum(hash(CAST(file_row_number AS VARCHAR) || chr(31) || "
        f"coalesce(CAST({ident(name)} AS VARCHAR), chr(0)))::HUGEINT)"
        for name in names
    )
    row = (
        connection.execute(
            f"SELECT {hashes} FROM read_parquet({lit(storage_path)}, file_row_number = true)"
        ).fetchone()
        or ()
    )
    groups: dict[Any, list[str]] = {}
    for name, digest in zip(names, row, strict=True):
        groups.setdefault(digest, []).append(name)
    return [group for group in groups.values() if len(group) > 1]


def skewness(
    connection: duckdb.DuckDBPyConnection, source: str, columns: list[ColumnView]
) -> dict[str, float | None]:
    numeric = [c for c in columns if c.type == "numeric_continuous"]
    if not numeric:
        return {}
    expressions = ", ".join(
        f"skewness(CAST({typed_sql(c.name, c.parser)} AS DOUBLE))" for c in numeric
    )
    row = connection.execute(f"SELECT {expressions} FROM {source}").fetchone() or ()
    return {
        column.name: (float(value) if value is not None and value == value else None)
        for column, value in zip(numeric, row, strict=True)
    }


def alerts_for(
    overview_rows: int,
    columns: list[ColumnView],
    duplicates: int,
    duplicate_groups: list[list[str]],
    skews: dict[str, float | None],
) -> list[Alert]:
    alerts: list[Alert] = []
    if duplicates:
        alerts.append(
            Alert(
                "duplicate_rows",
                "warning",
                f"{plural(duplicates, 'duplicate row')} ({_pct(duplicates, overview_rows)}%)",
            )
        )
    for group in duplicate_groups:
        alerts.append(
            Alert("duplicate_columns", "warning", f"Identical content: {', '.join(group)}", group)
        )
    ignored = [c.name for c in columns if c.type == "ignored" and not c.excluded]
    if ignored:
        alerts.append(
            Alert(
                "ignored",
                "info",
                f"{plural(len(ignored), 'empty or constant column')} ignored",
                ignored,
            )
        )
    review = [c.name for c in columns if c.confidence != "high" and not c.overridden]
    if review:
        alerts.append(
            Alert("to_review", "info", f"{plural(len(review), 'column type')} to confirm", review)
        )
    invalid = [c.name for c in columns if c.summary and c.summary.get("invalid_count")]
    if invalid:
        alerts.append(
            Alert(
                "invalid_values",
                "warning",
                f"Unreadable values in {plural(len(invalid), 'column')}",
                invalid,
            )
        )
    skewed = [
        name for name, value in skews.items() if value is not None and abs(value) > SKEW_ALERT
    ]
    if skewed:
        alerts.append(
            Alert(
                "skewed", "info", f"{plural(len(skewed), 'strongly skewed numeric column')}", skewed
            )
        )
    crowded = [
        c.name
        for c in columns
        if c.type == "categorical_nominal"
        and c.summary
        and (present := c.summary["rows"] - c.summary["null_count"]) >= 50
        and c.summary["distinct_count"] / present > HIGH_CARDINALITY
    ]
    if crowded:
        alerts.append(
            Alert(
                "high_cardinality",
                "warning",
                f"{plural(len(crowded), 'category', 'categories')} with mostly unique values",
                crowded,
            )
        )
    return alerts


def dataset_overview(
    connection: duckdb.DuckDBPyConnection,
    storage_path: str,
    size_bytes: int,
    columns: list[ColumnView],
) -> Overview:
    source = f"read_parquet({lit(storage_path)})"
    rows = int((connection.execute(f"SELECT count(*) FROM {source}").fetchone() or (0,))[0])
    used = [c for c in columns if not c.excluded]
    missing = sum(int(c.summary["null_count"]) for c in used if c.summary)
    duplicates = duplicate_rows(connection, source)
    comparable = [c.name for c in used if c.type != "ignored"]
    groups = duplicate_columns(connection, storage_path, comparable)
    skews = skewness(connection, source, used)
    stats = {
        c.name: ColumnStats(
            missing_pct=_pct(c.summary["null_count"], c.summary["rows"]) if c.summary else 0,
            distinct=int(c.summary["distinct_count"]) if c.summary else 0,
            skewness=skews.get(c.name),
        )
        for c in columns
    }
    return Overview(
        rows=rows,
        columns=len(columns),
        used_columns=len(used),
        missing_cells=missing,
        missing_pct=_pct(missing, rows * len(used)),
        duplicate_rows=duplicates,
        duplicate_columns=groups,
        size_bytes=size_bytes,
        types=dict(Counter(c.type for c in used)),
        alerts=alerts_for(rows, columns, duplicates, groups, skews),
        column_stats=stats,
    )
