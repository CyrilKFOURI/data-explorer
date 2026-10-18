"""Machine learning page: target candidates, training jobs, saved runs."""

import csv
import io
import json
import sqlite3
import threading
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import duckdb
import joblib
from pydantic import TypeAdapter

from app.core import db
from app.core.errors import AppError
from app.core.storage import Workspace
from app.domain.columns.service import ColumnService
from app.domain.filters.model import Condition
from app.domain.filters.scope import scoped_source, where_for
from app.domain.ml import classes as binning
from app.domain.ml import data as ml_data
from app.domain.ml import models as catalogue
from app.domain.ml import preparation as prep
from app.domain.ml import train as trainer
from app.domain.ml.data import NUMERIC, Field
from app.domain.ml.target import Candidate, Task, candidate

Stage = Literal["loading", "preparing", "training", "saving"]


class MlError(AppError):
    def __init__(self, message: str, code: str = "ml", status_code: int = 422) -> None:
        super().__init__(message, code=code, status_code=status_code)


@dataclass
class SettingView:
    key: str
    label: str
    kind: str
    default: Any
    level: str
    options: list[str]
    minimum: float | None
    maximum: float | None
    log: bool
    why: str
    shown_when: dict[str, list[str]] | None


@dataclass
class ModelView:
    key: str
    label: str
    family: str
    description: str
    tasks: list[str]
    settings: list[SettingView]


@dataclass
class Targets:
    candidates: list[Candidate]
    rows: int  # rows after the filters


@dataclass
class Run:
    """A trained model as the page shows it (stored as JSON next to the fitted pipeline)."""

    id: str
    dataset_id: str
    target: str
    created_at: str
    task: Task
    model: str
    settings: dict[str, Any]
    preparation: prep.Preparation
    train_rows: int
    test_rows: int
    rows: int
    sampled: bool
    seconds: float
    regression: trainer.RegressionResult | None
    classification: trainer.ClassificationResult | None
    coefficients: list[trainer.Coefficient]
    predictions: list[trainer.PredictionRow]
    primary: str
    score: float | None
    classes: binning.Classes | None = None


@dataclass
class RunSummary:
    id: str
    target: str
    task: str
    model: str
    settings: dict[str, Any]
    metric: str
    score: float | None
    seconds: float
    created_at: str
    classes: binning.Classes | None = None


@dataclass
class TrainingJob:
    id: str
    status: Literal["running", "done", "failed"]
    stage: Stage
    run_id: str | None = None
    error: str | None = None


RUN = TypeAdapter(Run)
KEPT_JOBS = 32


FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


def _cell(text: str) -> str:
    """A label that a spreadsheet would run as a formula gets a leading apostrophe; numbers
    (including negative ones) are left as they are."""
    try:
        float(text)
        return text
    except ValueError:
        return f"'{text}" if text.startswith(FORMULA_STARTS) else text


def _now() -> str:
    return datetime.now(UTC).isoformat()


class MlService:
    def __init__(self, columns: ColumnService, workspace: Workspace) -> None:
        self.columns = columns
        self.workspace = workspace
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml")
        self._jobs: OrderedDict[str, TrainingJob] = OrderedDict()
        self._lock = threading.Lock()

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.workspace.db_path)
        try:
            yield connection
        finally:
            connection.close()

    def _folder(self, dataset_id: str) -> Path:
        return self.workspace.dataset_dir(dataset_id) / "ml"

    # --- Catalogue and targets -----------------------------------------------------------------

    def catalogue(self, task: Task, rows: int, minority: float | None) -> list[ModelView]:
        context = catalogue.Context(rows, task, minority)
        return [
            ModelView(
                spec.key,
                spec.label,
                spec.family,
                spec.description,
                list(spec.tasks),
                [SettingView(**asdict(setting)) for setting in spec.settings(context)],
            )
            for spec in catalogue.CATALOGUE.values()
            if task in spec.tasks
        ]

    def _fields(self, dataset_id: str) -> tuple[list[Field], Any]:
        dataset = self.columns.ready(dataset_id)
        views = [v for v in self.columns.columns(dataset_id) if not v.excluded]
        fields = [Field(v.name, v.type, v.parser, v.role, v.order) for v in views]
        return fields, (dataset, views)

    def targets(self, dataset_id: str, conditions: list[Condition]) -> Targets:
        fields, (dataset, views) = self._fields(dataset_id)
        connection = duckdb.connect()
        try:
            source = scoped_source(
                dataset.storage_path, where_for(views, conditions), numbered=True
            )
            parts = ", ".join(
                f"count(DISTINCT {ml_data._expression(f)}), count({ml_data._expression(f)})"
                for f in fields
            )
            row = connection.execute(f"SELECT count(*), {parts} FROM {source}").fetchone() or ()
        finally:
            connection.close()
        total = int(row[0]) if row else 0
        found = []
        for i, fld in enumerate(fields):
            distinct, present = int(row[1 + 2 * i]), int(row[2 + 2 * i])
            missing = 1 - present / total if total else 1.0
            found.append(candidate(fld.name, fld.type, fld.role, distinct, missing, present))
        found.sort(key=lambda c: (c.task is None, not c.suggested))
        return Targets(found, total)

    # --- Training ------------------------------------------------------------------------------

    def start(
        self,
        dataset_id: str,
        target: str,
        model: str | None,
        settings: dict[str, Any] | None,
        conditions: list[Condition],
        choices: prep.Choices | None = None,
        classes: binning.Classes | None = None,
    ) -> TrainingJob:
        fields, field_, source = self._request(dataset_id, target, model, conditions, classes)
        job = TrainingJob(uuid.uuid4().hex[:12], "running", "loading")
        with self._lock:
            self._jobs[job.id] = job
            while len(self._jobs) > KEPT_JOBS:
                self._jobs.popitem(last=False)
        self._executor.submit(
            self._train,
            job,
            dataset_id,
            fields,
            field_,
            model,
            settings,
            source,
            conditions,
            choices,
            classes,
        )
        return job

    def _request(
        self,
        dataset_id: str,
        target: str,
        model: str | None,
        conditions: list[Condition],
        classes: binning.Classes | None = None,
    ) -> tuple[list[Field], Field, str]:
        fields, (dataset, views) = self._fields(dataset_id)
        by_name = {f.name: f for f in fields}
        if target not in by_name:
            raise MlError(f"Unknown or ignored column {target!r}.", "unknown_column")
        field_ = by_name[target]
        if field_.type in ("identifier", "text", "datetime"):
            raise MlError(f"{target!r} cannot be predicted: it is {field_.type}.", "bad_target")
        if model is not None and model not in catalogue.CATALOGUE:
            raise MlError(f"Unknown model {model!r}.", "unknown_model")
        if classes is not None and field_.type not in NUMERIC:
            raise MlError(
                f"{target!r} is not a number: it cannot be cut into classes.", "bad_classes"
            )
        source = scoped_source(dataset.storage_path, where_for(views, conditions), numbered=True)
        return fields, field_, source

    def _load(self, fields: list[Field], target: Field, source: str) -> tuple[ml_data.Frame, Task]:
        connection = duckdb.connect()
        try:
            frame = ml_data.load(connection, source, fields, target.name)
        finally:
            connection.close()
        if frame.rows < 15:
            raise MlError("Fewer than 15 rows have a target value.")
        distinct = len(set(frame.data[target.name].dropna().astype(str)))
        task = candidate(target.name, target.type, target.role, distinct, 0).task
        if task is None:
            raise MlError(f"{target.name!r} cannot be predicted.")
        return frame, task

    def preview(
        self,
        dataset_id: str,
        target: str,
        model: str | None,
        settings: dict[str, Any] | None,
        conditions: list[Condition],
        choices: prep.Choices | None,
        classes: binning.Classes | None = None,
    ) -> trainer.PreparationPreview:
        """The preparation the next training would use, and its first prepared rows."""
        fields, field_, source = self._request(dataset_id, target, model, conditions, classes)
        frame, task = self._load(fields, field_, source)
        if classes is not None:
            task = "binary" if len(classes.names) == 2 else "multiclass"
        try:
            return trainer.preview(
                frame.data,
                fields,
                field_,
                task,
                model or catalogue.default_model(task),
                settings,
                choices,
                classes=classes,
            )
        except (trainer.TrainingError, catalogue.SettingsError) as error:
            raise MlError(str(error)) from None

    def job(self, job_id: str) -> TrainingJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise MlError("This training is no longer followed: open the runs.", "unknown_job")
        return job

    def _train(
        self,
        job: TrainingJob,
        dataset_id: str,
        fields: list[Field],
        target: Field,
        model: str | None,
        settings: dict[str, Any] | None,
        source: str,
        conditions: list[Condition],
        choices: prep.Choices | None = None,
        classes: binning.Classes | None = None,
    ) -> None:
        try:
            frame, task = self._load(fields, target, source)
            if classes is not None:
                task = "binary" if len(classes.names) == 2 else "multiclass"
            job.stage = "preparing"
            key = model or catalogue.default_model(task)
            job.stage = "training"
            trained = trainer.train(
                frame.data,
                fields,
                target,
                task,
                key,
                settings,
                frame.rows,
                frame.sampled,
                choices=choices,
                classes=classes,
            )
            job.stage = "saving"
            job.run_id = self._save(dataset_id, target.name, trained, conditions)
            job.status = "done"
        except (MlError, trainer.TrainingError, catalogue.SettingsError, ValueError) as error:
            job.status, job.error = "failed", str(error)
        except Exception as error:
            job.status, job.error = "failed", f"Training failed: {error}"

    def _save(
        self, dataset_id: str, target: str, trained: trainer.Trained, conditions: list[Condition]
    ) -> str:
        run_id = uuid.uuid4().hex[:12]
        values = {f.name: getattr(trained, f.name) for f in fields(trained) if f.name != "pipeline"}
        run = Run(id=run_id, dataset_id=dataset_id, target=target, created_at=_now(), **values)
        folder = self._folder(dataset_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{run_id}.json").write_bytes(RUN.dump_json(run))
        joblib.dump(trained.pipeline, folder / f"{run_id}.joblib")
        with self._db() as connection, connection:
            connection.execute(
                "INSERT INTO ml_runs (id, dataset_id, target, task, model, settings, conditions,"
                " metric, score, seconds, created_at, classes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    dataset_id,
                    target,
                    trained.task,
                    trained.model,
                    json.dumps(trained.settings),
                    json.dumps([c.model_dump() for c in conditions]),
                    trained.primary,
                    trained.score,
                    trained.seconds,
                    run.created_at,
                    trained.classes.model_dump_json() if trained.classes else None,
                ),
            )
        return run_id

    # --- Runs ----------------------------------------------------------------------------------

    def runs(self, dataset_id: str, target: str | None = None) -> list[RunSummary]:
        self.columns.datasets.get(dataset_id)
        query = "SELECT * FROM ml_runs WHERE dataset_id = ?"
        params: list[Any] = [dataset_id]
        if target:
            query += " AND target = ?"
            params.append(target)
        with self._db() as connection:
            rows = connection.execute(query + " ORDER BY created_at DESC", params).fetchall()
        return [
            RunSummary(
                r["id"],
                r["target"],
                r["task"],
                r["model"],
                json.loads(r["settings"]),
                r["metric"],
                r["score"],
                r["seconds"],
                r["created_at"],
                binning.Classes.model_validate_json(r["classes"]) if r["classes"] else None,
            )
            for r in rows
        ]

    def distribution(
        self, dataset_id: str, column: str, conditions: list[Condition]
    ) -> binning.TargetDistribution:
        """A numeric target's distribution, for cutting it into classes in the browser."""
        _, field_, source = self._request(dataset_id, column, None, conditions)
        if field_.type not in NUMERIC:
            raise MlError(f"{column!r} is not a number.", "bad_classes")
        connection = duckdb.connect()
        try:
            return binning.distribution(connection, source, field_)
        finally:
            connection.close()

    def run(self, dataset_id: str, run_id: str) -> Run:
        path = self._folder(dataset_id) / f"{run_id}.json"
        if not path.is_file():
            raise MlError("Unknown run.", "unknown_run", 404)
        return RUN.validate_json(path.read_bytes())

    def predictions_csv(self, dataset_id: str, run_id: str) -> str:
        run = self.run(dataset_id, run_id)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["row", "actual", "predicted", "error", "probability", "correct"])
        for p in run.predictions:
            writer.writerow(
                [p.row, _cell(p.actual), _cell(p.predicted), p.error, p.probability, p.correct]
            )
        return buffer.getvalue()
