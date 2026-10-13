"""Overview and chart data of a dataset, read through the effective column types."""

from collections import OrderedDict
from typing import Any

import duckdb

from app.domain.charts.prepare import Chart, ChartParams, ColumnInput, prepare_chart
from app.domain.columns.service import ColumnService
from app.domain.datasets.service import NotFoundError
from app.domain.ingestion.sql import lit
from app.domain.profiling.overview import Overview, dataset_overview

CACHE_SIZE = 64


class ProfilingService:
    def __init__(self, columns: ColumnService) -> None:
        self.columns = columns
        # Overviews depend on the data and the column types only: cached per types_version.
        self._overviews: OrderedDict[tuple[Any, ...], Overview] = OrderedDict()

    def overview(self, dataset_id: str) -> Overview:
        dataset = self.columns.ready(dataset_id)
        views = self.columns.columns(dataset_id)
        excluded = tuple(sorted(c.name for c in views if c.excluded))
        key = (dataset_id, dataset.imported_at, dataset.types_version, excluded)
        if key in self._overviews:
            self._overviews.move_to_end(key)
            return self._overviews[key]
        connection = duckdb.connect()
        try:
            result = dataset_overview(
                connection, dataset.storage_path, dataset.size_bytes or 0, views
            )
        finally:
            connection.close()
        self._overviews[key] = result
        if len(self._overviews) > CACHE_SIZE:
            self._overviews.popitem(last=False)
        return result

    def chart(self, dataset_id: str, column: str, params: ChartParams) -> Chart:
        dataset = self.columns.ready(dataset_id)
        view = next((c for c in self.columns.columns(dataset_id) if c.name == column), None)
        if view is None:
            raise NotFoundError(f"Column {column!r}")
        connection = duckdb.connect()
        try:
            return prepare_chart(
                connection,
                f"read_parquet({lit(dataset.storage_path)})",
                ColumnInput(view.name, view.type, view.parser, view.order),
                params,
            )
        finally:
            connection.close()
