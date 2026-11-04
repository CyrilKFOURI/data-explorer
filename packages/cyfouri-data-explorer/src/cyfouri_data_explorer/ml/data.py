"""Read the columns of a dataset into a pandas frame, typed, through the active filters."""

from dataclasses import dataclass

import duckdb
import pandas as pd

from cyfouri_data_explorer.compare.analyze import label_sql, number_sql
from cyfouri_data_explorer.typing.parsers import typed_sql
from cyfouri_data_explorer.typing.types import AnalysisType, Parser
from cyfouri_data_explorer.variable.source import SEED

MAX_ROWS = 200_000  # training rows by default (a reproducible sample beyond)
NUMERIC = {"numeric_continuous", "numeric_discrete"}
CATEGORICAL = {"categorical_nominal", "categorical_ordinal", "boolean"}


@dataclass
class Field:
    name: str
    type: AnalysisType
    parser: Parser
    role: str | None = None
    order: list[str] | None = None


@dataclass
class Frame:
    data: pd.DataFrame  # one column per field, plus "__row" (row number in the file)
    rows: int  # rows after the filters with a target value
    sampled: bool


def _expression(field: Field) -> str:
    if field.type in NUMERIC:
        return number_sql(field)  # type: ignore[arg-type]
    if field.type == "datetime":
        return f"CAST({typed_sql(field.name, field.parser)} AS TIMESTAMP)"
    if field.type in CATEGORICAL:
        return label_sql(field)  # type: ignore[arg-type]
    return f"CAST({typed_sql(field.name, field.parser)} AS VARCHAR)"


def load(
    connection: duckdb.DuckDBPyConnection,
    source: str,
    fields: list[Field],
    target: str,
    limit: int | None = MAX_ROWS,
) -> Frame:
    """Rows with a target value; at most `limit` of them, drawn reproducibly."""
    aliases = {field.name: f"c{i}" for i, field in enumerate(fields)}
    selected = ", ".join(f"{_expression(f)} AS {aliases[f.name]}" for f in fields)
    relation = (
        f"(SELECT * FROM (SELECT {selected}, file_row_number AS __row FROM {source}) "
        f"WHERE {aliases[target]} IS NOT NULL)"
    )
    (rows,) = connection.execute(f"SELECT count(*) FROM {relation}").fetchone() or (0,)
    sampled = limit is not None and rows > limit
    order = f"ORDER BY hash(__row + {SEED}) LIMIT {limit}" if sampled else "ORDER BY __row"
    data = connection.execute(f"SELECT * FROM {relation} {order}").df()
    data.columns = [*(f.name for f in fields), "__row"]
    for field in fields:
        if field.type in NUMERIC:
            data[field.name] = pd.Series(
                pd.to_numeric(data[field.name], errors="coerce"), index=data.index, dtype=float
            )
    return Frame(data, int(rows), bool(sampled))
