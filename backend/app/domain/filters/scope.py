"""The rows an analysis reads: the dataset's Parquet copy, narrowed by the active filters."""

from collections.abc import Sequence
from typing import Protocol

from app.domain.filters.model import Condition
from app.domain.filters.sql import FilterColumn, filtered_source, where_sql
from app.domain.ingestion.sql import lit
from app.domain.typing.types import AnalysisType, Parser


class TypedColumn(Protocol):
    name: str
    type: AnalysisType
    parser: Parser


def where_for(columns: Sequence[TypedColumn], conditions: list[Condition]) -> str:
    """WHERE clause of the conditions, read through each column's effective type and parser."""
    if not conditions:
        return ""
    known = {c.name: FilterColumn(c.name, c.type, c.parser) for c in columns}
    return where_sql(conditions, known)


def scoped_source(storage_path: str, where: str, numbered: bool = False) -> str:
    """`numbered` keeps `file_row_number` (row numbers of the file, 0-based)."""
    options = ", file_row_number = true" if numbered else ""
    return filtered_source(f"read_parquet({lit(storage_path)}{options})", where)
