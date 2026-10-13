"""A filter is a list of conditions combined with AND; values of one condition combine with OR."""

import json
from typing import Literal

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from app.core.errors import AppError
from app.domain.typing.dates import DatePart

Operator = Literal[
    "eq",  # equal (numbers, text, dates)
    "gt",
    "gte",
    "lt",
    "lte",
    "between",  # low <= value <= high (numbers, dates)
    "in",  # one of `values` (categories, booleans, discrete numbers)
    "contains",
    "starts_with",
    "is_null",
    "part_in",  # a date part (`part`) is one of `values`, e.g. day_of_week in [1]
]

MAX_CONDITIONS = 50
MAX_VALUES = 1_000


class Condition(BaseModel):
    column: str = Field(min_length=1)
    op: Operator
    value: str | float | None = None
    low: str | float | None = None
    high: str | float | None = None
    values: list[str] = Field(default_factory=list, max_length=MAX_VALUES)
    part: DatePart | None = None
    negate: bool = False


Conditions = TypeAdapter(list[Condition])


class InvalidFilterError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_filter", status_code=422)


def parse_filters(raw: str | None) -> list[Condition]:
    """The `filters` query parameter: a JSON list of conditions (empty or absent = no filter)."""
    if not raw:
        return []
    try:
        conditions = Conditions.validate_python(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as error:
        raise InvalidFilterError(f"Invalid filters: {error}") from error
    if len(conditions) > MAX_CONDITIONS:
        raise InvalidFilterError(f"At most {MAX_CONDITIONS} filters.")
    return conditions


def filters_key(conditions: list[Condition]) -> str:
    """Stable text form, for cache keys."""
    return json.dumps([c.model_dump() for c in conditions], sort_keys=True)
