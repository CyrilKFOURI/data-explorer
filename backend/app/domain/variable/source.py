"""One column of a dataset, read through its parser, with the helpers every analysis needs.

The source must expose `file_row_number` (read_parquet(..., file_row_number=true)) so that
rows can be pointed at; statistics run on every row, tests and fits on a seeded sample.
"""

import math
from dataclasses import dataclass

import duckdb
import numpy as np

from app.domain.typing.parsers import typed_sql
from app.domain.typing.types import AnalysisType, Parser

SEED = 42


@dataclass
class VariableInput:
    name: str
    type: AnalysisType
    parser: Parser
    order: list[str] | None = None


def clean(value: object) -> float | None:
    """SQL/numpy number → JSON-safe float (NaN and infinities become None)."""
    if value is None:
        return None
    number = float(value)  # type: ignore[arg-type]
    return number if math.isfinite(number) else None


class VariableSource:
    def __init__(self, connection: duckdb.DuckDBPyConnection, source: str, column: VariableInput):
        self.connection = connection
        self.column = column
        typed = typed_sql(column.name, column.parser)
        self.values = f"(SELECT {typed} AS t, file_row_number AS row FROM {source})"
        # Finite numbers only: infinities are counted apart and kept out of the moments.
        self.numbers = (
            f"(SELECT CAST(t AS DOUBLE) AS x, row FROM {self.values} "
            "WHERE t IS NOT NULL AND isfinite(CAST(t AS DOUBLE)))"
        )

    def one(self, sql: str) -> tuple:
        return self.connection.execute(sql).fetchone() or ()

    def all(self, sql: str) -> list[tuple]:
        return self.connection.execute(sql).fetchall()

    def sample(self, size: int) -> np.ndarray:
        """Finite values, at most `size` of them, drawn reproducibly."""
        (count,) = self.one(f"SELECT count(*) FROM {self.numbers}")
        if count <= size:
            rows = self.all(f"SELECT x FROM {self.numbers}")
        else:
            # Hash of the row number: the same rows on every call, whatever the thread count.
            rows = self.all(
                f"SELECT x FROM {self.numbers} ORDER BY hash(row + {SEED}) LIMIT {size}"
            )
        return np.array([value for (value,) in rows], dtype=float)
