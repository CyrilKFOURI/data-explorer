"""Variable analyses of a dataset's column, read through its effective type; cached in memory."""

from collections import OrderedDict
from collections.abc import Callable
from typing import Any

import duckdb

from app.core.errors import AppError
from app.domain.columns.service import ColumnService
from app.domain.datasets.service import NotFoundError
from app.domain.ingestion.sql import lit
from app.domain.variable.analyze import NUMERIC, VariableProfile, analyze
from app.domain.variable.fitting import Fit, fit
from app.domain.variable.numeric import describe
from app.domain.variable.outliers import OutlierMethod, Outliers, outliers
from app.domain.variable.source import VariableInput, VariableSource

CACHE_SIZE = 32


class NotNumericError(AppError):
    def __init__(self, column: str) -> None:
        super().__init__(f"{column!r} is not numeric", code="not_numeric", status_code=422)


class VariableService:
    def __init__(self, columns: ColumnService) -> None:
        self.columns = columns
        self._cache: OrderedDict[tuple[Any, ...], Any] = OrderedDict()

    def _cached(self, key: tuple[Any, ...], compute: Callable[[], Any]) -> Any:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        value = compute()
        self._cache[key] = value
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)
        return value

    def _run(self, dataset_id: str, column: str, what: str, task: Callable[[VariableSource], Any]):
        dataset = self.columns.ready(dataset_id)
        view = next((c for c in self.columns.columns(dataset_id) if c.name == column), None)
        if view is None:
            raise NotFoundError(f"Column {column!r}")
        key = (
            dataset_id,
            dataset.imported_at,
            column,
            view.type,
            view.parser.model_dump_json(),
            what,
        )

        def compute() -> Any:
            connection = duckdb.connect()
            try:
                source = VariableSource(
                    connection,
                    f"read_parquet({lit(dataset.storage_path)}, file_row_number=true)",
                    VariableInput(view.name, view.type, view.parser, view.order),
                )
                return task(source)
            finally:
                connection.close()

        return self._cached(key, compute)

    @staticmethod
    def _numeric(source: VariableSource) -> None:
        if source.column.type not in NUMERIC:
            raise NotNumericError(source.column.name)

    def profile(self, dataset_id: str, column: str) -> VariableProfile:
        return self._run(dataset_id, column, "profile", analyze)

    def fit(self, dataset_id: str, column: str) -> Fit:
        def task(source: VariableSource) -> Fit:
            self._numeric(source)
            return fit(source, discrete=source.column.type == "numeric_discrete")

        return self._run(dataset_id, column, "fit", task)

    def outliers(self, dataset_id: str, column: str, method: OutlierMethod) -> Outliers:
        def task(source: VariableSource) -> Outliers:
            self._numeric(source)
            return outliers(source, describe(source), method)

        return self._run(dataset_id, column, f"outliers:{method}", task)
