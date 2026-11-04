"""Results as plain data: `to_dict()` for any result (JSON-safe), `to_pandas()` for the tabular
ones. The results themselves are the app's dataclasses, unchanged."""

from __future__ import annotations

import dataclasses
import datetime as dt
import enum
import math
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from pydantic import BaseModel

from cyfouri_data_explorer.catalog import ColumnView

if TYPE_CHECKING:
    from cyfouri_data_explorer.correlations.matrix import Matrix
    from cyfouri_data_explorer.kpi.compute import KpiResult
    from cyfouri_data_explorer.profiling.overview import Overview
    from cyfouri_data_explorer.rows.view import RowsPage


def to_dict(result: Any) -> Any:
    """A result as dicts, lists and plain numbers (NaN and infinities become None): ready for
    `json.dumps`."""
    if type(result).__name__ == "TrainedModel":
        return to_dict(result.result)  # its run, without the pipeline
    if dataclasses.is_dataclass(result) and not isinstance(result, type):
        return {
            f.name: to_dict(getattr(result, f.name))
            for f in dataclasses.fields(result)
            if f.name != "pipeline"
        }
    if isinstance(result, BaseModel):
        return to_dict(result.model_dump())
    if isinstance(result, dict):
        return {str(key): to_dict(value) for key, value in result.items()}
    if isinstance(result, list | tuple | set):
        return [to_dict(value) for value in result]
    if isinstance(result, np.ndarray):
        return to_dict(result.tolist())
    if isinstance(result, np.generic):
        return to_dict(result.item())
    if isinstance(result, float):
        return result if math.isfinite(result) else None
    if isinstance(result, enum.Enum):
        return result.value
    if isinstance(result, dt.date | dt.datetime | dt.time):
        return result.isoformat()
    if isinstance(result, Path):
        return str(result)
    if isinstance(result, pd.DataFrame):
        return to_dict(result.to_dict(orient="records"))
    return result


def _rows(items: list[Any]) -> pd.DataFrame:
    return pd.DataFrame([to_dict(item) for item in items])


def _matrix(matrix: Matrix) -> pd.DataFrame:
    names = [member.name for member in matrix.columns]
    return pd.DataFrame(matrix.values, index=names, columns=names, dtype=float)


def _overview(overview: Overview) -> pd.DataFrame:
    frame = pd.DataFrame({name: to_dict(stats) for name, stats in overview.column_stats.items()})
    return frame.T.rename_axis("column").reset_index()


def _page(page: RowsPage) -> pd.DataFrame:
    return pd.DataFrame(page.rows, columns=["row", *(c.name for c in page.columns)])


def _kpi(result: KpiResult) -> pd.DataFrame:
    labels = [p.label for p in result.periods]
    frames = []
    for line in result.series:
        if len(line.values) != len(labels):
            continue
        frames.append(
            pd.DataFrame(
                {
                    "measure": line.measure,
                    "split": line.g1,
                    "split2": line.g2,
                    "period": labels,
                    "value": line.values,
                }
            )
        )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _tables() -> list[tuple[type, Callable[[Any], pd.DataFrame], str]]:
    """Each tabular result and its table (imported here: machine learning loads on demand)."""
    from cyfouri_data_explorer.compare.analyze import Comparison
    from cyfouri_data_explorer.correlations.matrix import Matrix
    from cyfouri_data_explorer.correlations.service import Correlations
    from cyfouri_data_explorer.kpi.compute import KpiResult
    from cyfouri_data_explorer.ml.engine import Catalogue, Targets
    from cyfouri_data_explorer.ml.explain import Explanation
    from cyfouri_data_explorer.profiling.overview import Overview
    from cyfouri_data_explorer.rows.view import RowsPage
    from cyfouri_data_explorer.synthetic.plan import Plan
    from cyfouri_data_explorer.timeseries.forecasting import SeriesForecast
    from cyfouri_data_explorer.variable.fitting import Fit
    from cyfouri_data_explorer.variable.outliers import Outliers

    return [
        (RowsPage, _page, "the rows"),
        (Correlations, lambda r: _matrix(r.matrix), "the association matrix"),
        (Matrix, _matrix, "the association matrix"),
        (Overview, _overview, "per-column statistics"),
        (
            Fit,
            lambda r: _rows(r.laws).drop(columns=["density", "quantiles"], errors="ignore"),
            "laws",
        ),
        (Outliers, lambda r: _rows(r.rules), "the rule of each method"),
        (Comparison, lambda r: _rows(r.tests), "the tests"),
        (Targets, lambda r: _rows(r.candidates), "every column as a target"),
        (
            Catalogue,
            lambda r: _rows(r.models).loc[:, ["key", "label", "family", "installed"]],
            "models",
        ),
        (
            Explanation,
            lambda r: _rows(r.permutation.items) if r.permutation else pd.DataFrame(),
            "permutation importance",
        ),
        (SeriesForecast, lambda r: _rows(r.results), "every model's scores"),
        (Plan, lambda r: _rows(r.columns), "the plan of each column"),
        (KpiResult, _kpi, "values per measure, split and period"),
    ]


def to_pandas(result: Any) -> pd.DataFrame:
    """The table of a tabular result: rows, association matrix, per-column statistics, laws,
    tests, targets, models, permutation importance, forecasts, a KPI's values, the types."""
    if isinstance(result, list) and all(isinstance(item, ColumnView) for item in result):
        return _rows(result).drop(columns=["summary"], errors="ignore")
    tables = _tables()
    for kind, table, _what in tables:
        if isinstance(result, kind):
            return table(result)
    known = ", ".join(f"{kind.__name__} ({what})" for kind, _table, what in tables)
    raise TypeError(f"No table for {type(result).__name__}: to_pandas() knows {known}.")
