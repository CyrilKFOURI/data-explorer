"""KPI builder: suggestions, computation through the page filters, and saved KPIs (SQLite)."""

import json
import sqlite3
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import duckdb

from app.core import db
from app.core.errors import AppError
from app.core.storage import Workspace
from app.domain.columns.service import ColumnService
from app.domain.datasets.repository import now
from app.domain.datasets.service import NotFoundError
from app.domain.filters.model import Condition, filters_key
from app.domain.filters.scope import scoped_source, where_for
from app.domain.kpi.compute import KpiResult, compute
from app.domain.kpi.definition import Definition
from app.domain.kpi.suggest import split_candidates, suggest

CACHE_SIZE = 16


@dataclass
class SuggestedKpi:
    rule: str
    name: str
    definition: Definition


@dataclass
class Suggestions:
    kpis: list[SuggestedKpi]
    splits: list[str]  # the best columns to split by, best first


@dataclass
class SavedKpi:
    id: str
    name: str
    definition: Definition
    created_at: str
    updated_at: str


def _saved(row: sqlite3.Row) -> SavedKpi:
    return SavedKpi(
        row["id"],
        row["name"],
        Definition.model_validate(json.loads(row["definition"])),
        row["created_at"],
        row["updated_at"],
    )


def _name(name: str) -> str:
    name = name.strip()
    if not name:
        raise AppError("Give the KPI a name.", code="invalid_name", status_code=422)
    return name


class KpiService:
    def __init__(self, columns: ColumnService, workspace: Workspace) -> None:
        self.columns = columns
        self.workspace = workspace
        self._cache: OrderedDict[tuple[Any, ...], KpiResult] = OrderedDict()

    def clear(self) -> None:
        self._cache.clear()

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.workspace.db_path)
        try:
            yield connection
        finally:
            connection.close()

    def _views(self, dataset_id: str) -> list[Any]:
        return [v for v in self.columns.columns(dataset_id) if not v.excluded]

    # --- Automatic start -------------------------------------------------------------------------

    def suggestions(self, dataset_id: str) -> Suggestions:
        views = self._views(dataset_id)
        found = suggest(views)
        return Suggestions(
            [SuggestedKpi(s.rule, s.name, s.definition) for s in found], split_candidates(views)
        )

    # --- Compute ---------------------------------------------------------------------------------

    def compute(
        self, dataset_id: str, definition: Definition, conditions: list[Condition]
    ) -> KpiResult:
        dataset = self.columns.ready(dataset_id)
        views = self._views(dataset_id)
        if definition.time is not None and not definition.time.page_filters:
            conditions = []  # the KPI only sees its own period
        data = definition.model_dump(mode="json", exclude={"view"})  # display needs no recompute
        key = (
            dataset_id,
            dataset.imported_at,
            json.dumps(data, sort_keys=True),
            tuple(
                (v.name, v.type, v.role, v.parser.model_dump_json(), str(v.order)) for v in views
            ),
            filters_key(conditions),
        )
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        connection = duckdb.connect()
        try:
            source = scoped_source(dataset.storage_path, where_for(views, conditions))
            result = compute(connection, source, views, definition)
        finally:
            connection.close()
        self._cache[key] = result
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)
        return result

    # --- Saved KPIs ------------------------------------------------------------------------------

    def all(self, dataset_id: str) -> list[SavedKpi]:
        self.columns.datasets.get(dataset_id)
        with self._db() as connection:
            rows = connection.execute(
                "SELECT * FROM kpi_definitions WHERE dataset_id = ? "
                "ORDER BY updated_at DESC, name COLLATE NOCASE",
                (dataset_id,),
            ).fetchall()
        return [_saved(row) for row in rows]

    def get(self, dataset_id: str, kpi_id: str) -> SavedKpi:
        with self._db() as connection:
            row = connection.execute(
                "SELECT * FROM kpi_definitions WHERE id = ? AND dataset_id = ?",
                (kpi_id, dataset_id),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"KPI {kpi_id!r}")
        return _saved(row)

    def create(self, dataset_id: str, name: str, definition: Definition) -> SavedKpi:
        self.columns.datasets.get(dataset_id)
        kpi_id = uuid.uuid4().hex[:12]
        stamp = now()
        with self._db() as connection, connection:
            connection.execute(
                "INSERT INTO kpi_definitions (id, dataset_id, name, definition, created_at, "
                "updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    kpi_id,
                    dataset_id,
                    _name(name),
                    definition.model_dump_json(by_alias=True),
                    stamp,
                    stamp,
                ),
            )
        return self.get(dataset_id, kpi_id)

    def update(
        self, dataset_id: str, kpi_id: str, name: str | None, definition: Definition | None
    ) -> SavedKpi:
        current = self.get(dataset_id, kpi_id)
        with self._db() as connection, connection:
            connection.execute(
                "UPDATE kpi_definitions SET name = ?, definition = ?, updated_at = ? WHERE id = ?",
                (
                    _name(name) if name is not None else current.name,
                    (definition or current.definition).model_dump_json(by_alias=True),
                    now(),
                    kpi_id,
                ),
            )
        return self.get(dataset_id, kpi_id)

    def duplicate(self, dataset_id: str, kpi_id: str) -> SavedKpi:
        current = self.get(dataset_id, kpi_id)
        return self.create(dataset_id, f"{current.name} (copy)", current.definition)

    def delete(self, dataset_id: str, kpi_id: str) -> None:
        with self._db() as connection, connection:
            deleted = connection.execute(
                "DELETE FROM kpi_definitions WHERE id = ? AND dataset_id = ?",
                (kpi_id, dataset_id),
            ).rowcount
        if not deleted:
            raise NotFoundError(f"KPI {kpi_id!r}")
