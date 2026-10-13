import duckdb
import pytest

from app.domain.filters.model import Condition, InvalidFilterError, parse_filters
from app.domain.filters.sql import FilterColumn, where_sql
from app.domain.typing.types import Parser

RAW = Parser(kind="raw")
COLUMNS = {
    "price": FilterColumn("price", "numeric_continuous", Parser(kind="number", decimal=",")),
    "kids": FilterColumn("kids", "numeric_discrete", RAW),
    "country": FilterColumn("country", "categorical_nominal", RAW),
    "active": FilterColumn("active", "boolean", RAW),
    "comment": FilterColumn("comment", "text", RAW),
    "day": FilterColumn("day", "datetime", RAW),
    "junk": FilterColumn("junk", "ignored", RAW),
}


@pytest.fixture
def connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(
        """
        CREATE TABLE t AS SELECT * FROM (VALUES
            (1, '79,50', 0, 'FR', true, 'Great value', TIMESTAMP '2024-01-01 10:00'),
            (2, '141,62', 2, 'BE', false, 'Too long 100%', TIMESTAMP '2024-01-02 09:00'),
            (3, '38,64', 1, 'FR', NULL, NULL, TIMESTAMP '2024-01-08 12:00'),
            (4, NULL, 3, 'ES', true, 'it''s fine', NULL),
            (5, '250,00', 2, NULL, false, 'great_deal', TIMESTAMP '2024-02-05 18:30')
        ) AS v(id, price, kids, country, active, comment, day)
        """
    )
    return con


def ids(con: duckdb.DuckDBPyConnection, *conditions: Condition) -> list[int]:
    where = where_sql(list(conditions), COLUMNS)
    rows = con.execute(f"SELECT id FROM t WHERE {where} ORDER BY id").fetchall()
    return [row[0] for row in rows]


def c(column: str, op: str, **kwargs) -> Condition:
    return Condition.model_validate({"column": column, "op": op, **kwargs})


def test_numbers_compare_typed_values(connection: duckdb.DuckDBPyConnection) -> None:
    # "79,50" is read through the column's parser: 79.5 > 50, compared as numbers.
    assert ids(connection, c("price", "gt", value=100)) == [2, 5]
    assert ids(connection, c("price", "between", low=50, high=150)) == [1, 2]


def test_negation_excludes_empty_values(connection: duckdb.DuckDBPyConnection) -> None:
    outside = c("price", "between", low=50, high=150, negate=True)

    assert ids(connection, outside) == [3, 5]  # row 4 has no price: never kept


def test_conditions_combine_with_and_values_with_or(connection: duckdb.DuckDBPyConnection) -> None:
    countries = c("country", "in", values=["FR", "BE"])

    assert ids(connection, countries) == [1, 2, 3]
    assert ids(connection, countries, c("kids", "gte", value=1)) == [2, 3]
    assert ids(connection, c("country", "in", values=["FR"], negate=True)) == [2, 4]


def test_booleans_and_discrete_values(connection: duckdb.DuckDBPyConnection) -> None:
    assert ids(connection, c("active", "in", values=["True"])) == [1, 4]
    assert ids(connection, c("kids", "in", values=["2", "3"])) == [2, 4, 5]


def test_empty_and_not_empty(connection: duckdb.DuckDBPyConnection) -> None:
    assert ids(connection, c("country", "is_null")) == [5]
    assert ids(connection, c("country", "is_null", negate=True)) == [1, 2, 3, 4]


def test_text_search_escapes_wildcards(connection: duckdb.DuckDBPyConnection) -> None:
    assert ids(connection, c("comment", "contains", value="GREAT")) == [1, 5]
    assert ids(connection, c("comment", "contains", value="_")) == [5]  # literal underscore
    assert ids(connection, c("comment", "contains", value="100%")) == [2]
    assert ids(connection, c("comment", "starts_with", value="it's")) == [4]


def test_dates_and_date_parts(connection: duckdb.DuckDBPyConnection) -> None:
    assert ids(connection, c("day", "lt", value="2024-01-05")) == [1, 2]
    assert ids(connection, c("day", "part_in", part="day_of_week", values=["1"])) == [1, 3, 5]
    assert ids(connection, c("day", "part_in", part="month", values=["2"])) == [5]
    assert ids(connection, c("day", "part_in", part="hour", values=["9", "10"])) == [1, 2]


def test_values_cannot_inject_sql(connection: duckdb.DuckDBPyConnection) -> None:
    sneaky = c("country", "in", values=["FR') OR 1=1 --"])

    assert ids(connection, sneaky) == []
    with pytest.raises(InvalidFilterError):
        ids(connection, c("price", "gt", value="1; DROP TABLE t"))


@pytest.mark.parametrize(
    ("condition", "message"),
    [
        (c("nope", "eq", value=1), "Unknown column"),
        (c("country", "gt", value=1), "can't use"),
        (c("junk", "is_null"), "ignored"),
        (c("country", "in", values=[]), "at least one value"),
        (c("day", "eq", value="13/45/2024"), "ISO date"),
        (c("price", "gt", value="inf"), "finite"),
    ],
)
def test_invalid_conditions_are_explained(condition: Condition, message: str) -> None:
    with pytest.raises(InvalidFilterError, match=message):
        where_sql([condition], COLUMNS)


def test_filters_parameter() -> None:
    assert parse_filters(None) == []
    assert parse_filters('[{"column": "a", "op": "is_null"}]')[0].column == "a"
    with pytest.raises(InvalidFilterError):
        parse_filters("not json")
    with pytest.raises(InvalidFilterError):
        parse_filters('[{"column": "a", "op": "drop"}]')
