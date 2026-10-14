"""Comparisons of a dataset's columns, read through their effective types and the active filters."""

from collections import OrderedDict
from typing import Any

import duckdb

from app.domain.columns.service import ColumnService
from app.domain.compare.analyze import CompareColumn, Comparison, NotComparableError, compare
from app.domain.filters.model import Condition, filters_key
from app.domain.filters.scope import scoped_source, where_for

CACHE_SIZE = 32


class CompareService:
    def __init__(self, columns: ColumnService) -> None:
        self.columns = columns
        self._cache: OrderedDict[tuple[Any, ...], Comparison] = OrderedDict()

    def compare(
        self,
        dataset_id: str,
        x: str,
        y: str,
        z: str | None = None,
        color: str | None = None,
        conditions: list[Condition] | None = None,
    ) -> Comparison:
        conditions = conditions or []
        dataset = self.columns.ready(dataset_id)
        views = {view.name: view for view in self.columns.columns(dataset_id)}

        def pick(name: str | None) -> CompareColumn | None:
            if name is None:
                return None
            view = views.get(name)
            if view is None or view.excluded:
                raise NotComparableError(f"Unknown or excluded column {name!r}.")
            return CompareColumn(view.name, view.type, view.parser, view.order)

        chosen = [pick(name) for name in (x, y, z, color)]
        key = (
            dataset_id,
            dataset.imported_at,
            tuple((c.name, c.type, c.parser.model_dump_json()) if c else None for c in chosen),
            filters_key(conditions),
        )
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        where = where_for(list(views.values()), conditions)
        connection = duckdb.connect()
        try:
            first, second, third, fourth = chosen
            assert first is not None and second is not None
            result = compare(
                connection,
                scoped_source(dataset.storage_path, where, numbered=True),
                first,
                second,
                third,
                fourth,
            )
        finally:
            connection.close()
        self._cache[key] = result
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)
        return result
