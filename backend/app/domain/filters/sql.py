"""Conditions → SQL over each column's typed value (its parser), every value escaped or cast.

Comparisons follow SQL: a negated condition never keeps empty values, except `is_null` negated
(= "is not empty").
"""

import math
from datetime import datetime

from app.domain.filters.model import Condition, InvalidFilterError
from app.domain.ingestion.sql import lit
from app.domain.typing.dates import part_sql
from app.domain.typing.parsers import typed_sql
from app.domain.typing.types import AnalysisType, Parser

NUMERIC = ("numeric_continuous", "numeric_discrete")
CATEGORICAL = ("categorical_nominal", "categorical_ordinal")
TEXTUAL = ("text", "identifier", *CATEGORICAL)

ALLOWED: dict[str, tuple[str, ...]] = {
    "numeric_continuous": ("eq", "gt", "gte", "lt", "lte", "between", "is_null"),
    "numeric_discrete": ("eq", "gt", "gte", "lt", "lte", "between", "in", "is_null"),
    "categorical_nominal": ("in", "eq", "contains", "starts_with", "is_null"),
    "categorical_ordinal": ("in", "eq", "contains", "starts_with", "is_null"),
    "boolean": ("in", "is_null"),
    "text": ("eq", "contains", "starts_with", "in", "is_null"),
    "identifier": ("eq", "contains", "starts_with", "in", "is_null"),
    "datetime": ("eq", "gt", "gte", "lt", "lte", "between", "part_in", "is_null"),
}
COMPARISONS = {"eq": "=", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}


class FilterColumn:
    """What a condition needs to know about its column."""

    def __init__(self, name: str, analysis_type: AnalysisType, parser: Parser) -> None:
        self.name = name
        self.type = analysis_type
        self.parser = parser


def _number(value: object, column: str) -> str:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise InvalidFilterError(f"{column!r}: {value!r} is not a number.") from None
    if not math.isfinite(number):
        raise InvalidFilterError(f"{column!r}: {value!r} is not a finite number.")
    return repr(number)


def _integer(value: object, column: str) -> str:
    try:
        return str(int(str(value)))
    except ValueError:
        raise InvalidFilterError(f"{column!r}: {value!r} is not a whole number.") from None


def _timestamp(value: object, column: str) -> str:
    try:
        moment = datetime.fromisoformat(str(value))
    except ValueError:
        raise InvalidFilterError(f"{column!r}: {value!r} is not an ISO date.") from None
    return f"TIMESTAMP {lit(moment.isoformat(sep=' '))}"


def _text(value: object, column: str) -> str:
    if value is None:
        raise InvalidFilterError(f"{column!r}: a value is required.")
    return lit(str(value))


def _like(value: object, column: str) -> str:
    """Escaped LIKE pattern body (no wildcards from the user)."""
    text = str(value if value is not None else "")
    if not text:
        raise InvalidFilterError(f"{column!r}: a value is required.")
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _label(typed: str, analysis_type: str) -> str:
    """The value as the charts label it (value_label): what `in` compares against."""
    if analysis_type == "boolean":
        return f"(CASE WHEN {typed} THEN 'True' WHEN NOT {typed} THEN 'False' END)"
    return f"CAST({typed} AS VARCHAR)"


def condition_sql(condition: Condition, column: FilterColumn) -> str:
    kind = column.type
    if kind == "ignored":
        raise InvalidFilterError(f"{column.name!r} is ignored: it can't be filtered.")
    if condition.op not in ALLOWED[kind]:
        raise InvalidFilterError(f"{column.name!r} ({kind}) can't use {condition.op!r}.")
    typed = typed_sql(column.name, column.parser)
    if condition.op == "is_null":
        return f"({typed}) IS NOT NULL" if condition.negate else f"({typed}) IS NULL"

    if kind in NUMERIC:
        value_of = _number
        subject = f"CAST({typed} AS DOUBLE)"
    elif kind == "datetime":
        value_of = _timestamp
        subject = f"CAST({typed} AS TIMESTAMP)"
    else:
        value_of = _text
        subject = f"CAST({typed} AS VARCHAR)"

    op = condition.op
    if op in COMPARISONS:
        sql = f"{subject} {COMPARISONS[op]} {value_of(condition.value, column.name)}"
    elif op == "between":
        low, high = (value_of(v, column.name) for v in (condition.low, condition.high))
        sql = f"{subject} BETWEEN {low} AND {high}"
    elif op in ("contains", "starts_with"):
        body = _like(condition.value, column.name)
        pattern = f"%{body}%" if op == "contains" else f"{body}%"
        sql = f"lower({subject}) LIKE lower({lit(pattern)}) ESCAPE '\\'"
    elif op == "in":
        if not condition.values:
            raise InvalidFilterError(f"{column.name!r}: pick at least one value.")
        if kind == "numeric_discrete":
            listed = ", ".join(_number(v, column.name) for v in condition.values)
            sql = f"{subject} IN ({listed})"
        else:
            listed = ", ".join(lit(v) for v in condition.values)
            sql = f"{_label(typed, kind)} IN ({listed})"
    else:  # part_in
        if condition.part is None or not condition.values:
            raise InvalidFilterError(f"{column.name!r}: pick a date part and at least one value.")
        listed = ", ".join(
            lit(v) if condition.part == "year_month" else _integer(v, column.name)
            for v in condition.values
        )
        sql = f"{part_sql(typed, condition.part)} IN ({listed})"
    # Negation keeps SQL's three-valued logic explicit: empty values are never kept.
    return f"(({typed}) IS NOT NULL AND NOT ({sql}))" if condition.negate else f"({sql})"


def where_sql(conditions: list[Condition], columns: dict[str, FilterColumn]) -> str:
    """AND of every condition; "" when there is none."""
    parts = []
    for condition in conditions:
        column = columns.get(condition.column)
        if column is None:
            raise InvalidFilterError(f"Unknown column {condition.column!r}.")
        parts.append(condition_sql(condition, column))
    return " AND ".join(parts)


def filtered_source(base: str, where: str) -> str:
    """A relation of the base rows that pass the filter (the base itself without filter)."""
    return f"(SELECT * FROM {base} WHERE {where})" if where else base
