"""Detect, list and correct the columns of a dataset."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, cast

import duckdb
from pydantic import BaseModel

from app.core import db
from app.core.errors import AppError
from app.core.storage import Workspace
from app.domain.columns import repository as repo
from app.domain.columns.repository import ColumnRecord
from app.domain.datasets import repository as datasets_repo
from app.domain.datasets.repository import DatasetRecord, now
from app.domain.datasets.service import DatasetService, NotFoundError
from app.domain.ingestion.sql import lit
from app.domain.typing.conversion import parser_for
from app.domain.typing.engine import detect_columns
from app.domain.typing.knowledge_base import load
from app.domain.typing.summary import summarize
from app.domain.typing.types import AnalysisType, ColumnDetection, Confidence, Parser


class ColumnChange(BaseModel):
    """A correction of one column. `None` fields are left unchanged."""

    name: str
    type: AnalysisType | None = None
    role: str | None = None  # "" = no role
    excluded: bool | None = None
    order: list[str] | None = None
    reset: bool = False


@dataclass
class ColumnView:
    name: str
    position: int
    storage_dtype: str
    type: AnalysisType
    role: str | None
    parser: Parser
    order: list[str] | None
    detected_type: AnalysisType
    detected_role: str | None
    confidence: Confidence
    reasons: list[str]
    overridden: bool
    excluded: bool
    summary: dict[str, Any] | None


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


def _parser(value: str | None) -> Parser | None:
    return Parser.model_validate_json(value) if value else None


def effective(record: ColumnRecord) -> tuple[AnalysisType, str | None, Parser, list[str] | None]:
    analysis_type = cast(AnalysisType, record.user_type or record.detected_type)
    role = record.detected_role if record.user_role is None else (record.user_role or None)
    parser = _parser(record.user_parser) or Parser.model_validate_json(record.detected_parser)
    order = _loads(record.user_order) or _loads(record.detected_order)
    return analysis_type, role, parser, order


def to_view(record: ColumnRecord) -> ColumnView:
    analysis_type, role, parser, order = effective(record)
    return ColumnView(
        name=record.name,
        position=record.position,
        storage_dtype=record.storage_dtype,
        type=analysis_type,
        role=role,
        parser=parser,
        order=order,
        detected_type=cast(AnalysisType, record.detected_type),
        detected_role=record.detected_role,
        confidence=cast(Confidence, record.confidence),
        reasons=json.loads(record.reasons),
        overridden=any(
            value is not None for value in (record.user_type, record.user_role, record.user_order)
        ),
        excluded=bool(record.excluded),
        summary=_loads(record.summary),
    )


def detection_record(dataset_id: str, detection: ColumnDetection) -> ColumnRecord:
    return ColumnRecord(
        dataset_id=dataset_id,
        name=detection.name,
        position=detection.position,
        storage_dtype=detection.storage_dtype,
        detected_type=detection.type,
        detected_role=detection.role,
        detected_parser=detection.parser.model_dump_json(),
        detected_order=json.dumps(detection.order) if detection.order else None,
        candidates=json.dumps(
            {kind: parser.model_dump() for kind, parser in detection.candidates.items()}
        ),
        confidence=detection.confidence,
        reasons=json.dumps(detection.reasons),
    )


class ColumnService:
    def __init__(self, workspace: Workspace, datasets: DatasetService) -> None:
        self.workspace = workspace
        self.datasets = datasets

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.workspace.db_path)
        try:
            yield connection
        finally:
            connection.close()

    def _ready(self, dataset_id: str) -> DatasetRecord:
        record = self.datasets.get(dataset_id)
        if record.status != "ready":
            raise AppError("This dataset is not ready yet.", code="not_ready", status_code=409)
        return record

    @staticmethod
    def _summarize(
        storage_path: str, record: ColumnRecord, connection: duckdb.DuckDBPyConnection | None = None
    ) -> str:
        analysis_type, _role, parser, order = effective(record)
        own = connection is None
        duck = connection or duckdb.connect()
        try:
            source = f"read_parquet({lit(storage_path)})"
            summary = summarize(duck, source, record.name, analysis_type, parser, order)
        finally:
            if own:
                duck.close()
        return json.dumps(summary)

    # --- Detection -----------------------------------------------------------------------------

    def detect_storage(self, dataset_id: str, storage_path: str) -> list[ColumnView]:
        """Detect all columns of a stored dataset, keeping the user's corrections."""
        duck = duckdb.connect()
        try:
            detections = detect_columns(duck, f"read_parquet({lit(storage_path)})")
            with self._db() as sqlite_connection:
                previous = {r.name: r for r in repo.list_columns(sqlite_connection, dataset_id)}
                records = []
                for detection in detections:
                    record = detection_record(dataset_id, detection)
                    if old := previous.get(detection.name):
                        for field in repo.USER_FIELDS:
                            setattr(record, field, getattr(old, field))
                    record.summary = self._summarize(storage_path, record, duck)
                    records.append(record)
                repo.replace_columns(sqlite_connection, dataset_id, records)
        finally:
            duck.close()
        return [to_view(record) for record in records]

    def detect(self, dataset_id: str) -> list[ColumnView]:
        return self.detect_storage(dataset_id, self._ready(dataset_id).storage_path)

    def columns(self, dataset_id: str) -> list[ColumnView]:
        dataset = self._ready(dataset_id)
        with self._db() as connection:
            records = repo.list_columns(connection, dataset_id)
        if not records:
            return self.detect_storage(dataset_id, dataset.storage_path)
        return [to_view(record) for record in records]

    # --- Corrections ---------------------------------------------------------------------------

    def update(self, dataset_id: str, changes: list[ColumnChange]) -> list[ColumnView]:
        dataset = self._ready(dataset_id)
        valid_roles = {role.id for role in load().roles}
        types_changed = False
        with self._db() as connection:
            for change in changes:
                record = repo.get_column(connection, dataset_id, change.name)
                if record is None:
                    raise NotFoundError(f"Column {change.name!r}")
                before = effective(record)
                self._apply(record, change, valid_roles)
                after = effective(record)
                if before[0] != after[0] or before[2] != after[2]:
                    types_changed = True
                if before != after:
                    record.summary = self._summarize(dataset.storage_path, record)
                repo.update_column(
                    connection,
                    dataset_id,
                    record.name,
                    **{field: getattr(record, field) for field in (*repo.USER_FIELDS, "summary")},
                )
            if types_changed:
                datasets_repo.update_dataset(
                    connection,
                    dataset_id,
                    types_version=self._types_version(connection, dataset_id) + 1,
                )
            records = repo.list_columns(connection, dataset_id)
        return [to_view(record) for record in records]

    @staticmethod
    def _types_version(connection: sqlite3.Connection, dataset_id: str) -> int:
        row = connection.execute(
            "SELECT types_version FROM datasets WHERE id = ?", (dataset_id,)
        ).fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _apply(record: ColumnRecord, change: ColumnChange, valid_roles: set[str]) -> None:
        if change.reset:
            record.user_type = record.user_role = record.user_parser = record.user_order = None
        if change.type is not None:
            detected_type = cast(AnalysisType, record.detected_type)
            if change.type == detected_type:
                record.user_type = record.user_parser = None
            else:
                candidates = {
                    kind: Parser.model_validate(parser)
                    for kind, parser in json.loads(record.candidates).items()
                }
                parser = parser_for(
                    change.type,
                    candidates,
                    detected_type,
                    Parser.model_validate_json(record.detected_parser),
                )
                record.user_type = change.type
                record.user_parser = parser.model_dump_json()
        if change.role is not None:
            if change.role and change.role not in valid_roles:
                raise AppError(
                    f"Unknown role {change.role!r}", code="invalid_role", status_code=422
                )
            record.user_role = None if change.role == (record.detected_role or "") else change.role
        if change.excluded is not None:
            record.excluded = int(change.excluded)
        if change.order is not None:
            record.user_order = json.dumps(change.order) if change.order else None

    def conversion(self, dataset_id: str, column: str, target: AnalysisType) -> tuple[Parser, dict]:
        """What the column would look like in another type, without saving anything."""
        dataset = self._ready(dataset_id)
        with self._db() as connection:
            record = repo.get_column(connection, dataset_id, column)
        if record is None:
            raise NotFoundError(f"Column {column!r}")
        self._apply(record, ColumnChange(name=column, type=target), set())
        _type, _role, parser, _order = effective(record)
        return parser, json.loads(self._summarize(dataset.storage_path, record))

    def mark_reviewed(self, dataset_id: str) -> DatasetRecord:
        self._ready(dataset_id)
        with self._db() as connection:
            datasets_repo.update_dataset(connection, dataset_id, types_reviewed_at=now())
        return self.datasets.get(dataset_id)
