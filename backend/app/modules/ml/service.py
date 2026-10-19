"""Machine learning page: target candidates, training jobs, saved runs."""

import csv
import io
import json
import sqlite3
import threading
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

import duckdb
import joblib
import pandas as pd
from pydantic import BaseModel, TypeAdapter
from pydantic import Field as PydanticField

from app.core import db
from app.core.errors import AppError
from app.core.storage import Workspace
from app.domain.columns.service import ColumnService
from app.domain.filters.model import Condition
from app.domain.filters.scope import scoped_source, where_for
from app.domain.ml import classes as binning
from app.domain.ml import data as ml_data
from app.domain.ml import evaluate
from app.domain.ml import explain as explainer
from app.domain.ml import models as catalogue
from app.domain.ml import preparation as prep
from app.domain.ml import train as trainer
from app.domain.ml import tune as tuner
from app.domain.ml.catalog import Context as ModelContext
from app.domain.ml.catalog.spaces import Param
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
    shown_when: dict[str, list[Any]] | None
    group: str
    param: str
    option_labels: dict[str, str]


@dataclass
class RuleView:
    when: dict[str, list[Any]]
    setting: str
    allowed: list[Any]
    reason: str


@dataclass
class ModelView:
    key: str
    label: str
    family: str
    description: str
    tasks: list[str]
    settings: list[SettingView]
    rules: list[RuleView]
    badges: list[str]
    installed: bool
    unavailable: str | None  # why it cannot run on this data
    probabilities: bool
    space: list[Param]  # where the optimizer searches (empty: nothing to tune)


@dataclass
class Recommendation:
    key: str
    why: str


@dataclass
class Catalogue:
    families: list[str]
    models: list[ModelView]
    recommended: list[Recommendation]
    metrics: list[str]  # every metric of the problem, the default first
    default_metric: str
    compare: list[str]  # models compared by default: one per suitable family


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
    scores: dict[str, float | None] = field(default_factory=dict)
    cross_validation: trainer.CrossValidation | None = None
    importances: list[trainer.Importance] = field(default_factory=list)
    validation: evaluate.Validation = field(default_factory=evaluate.Validation)
    evaluation_rows: list[int] = field(default_factory=list)


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
    greater_is_better: bool = True
    label: str = ""  # the model's name in the catalogue
    validation: evaluate.Validation = field(default_factory=evaluate.Validation)


@dataclass
class CompareItem:
    key: str
    label: str
    status: Literal["waiting", "running", "done", "failed"] = "waiting"
    run_id: str | None = None
    score: float | None = None
    seconds: float | None = None
    error: str | None = None


@dataclass
class CompareJob:
    id: str
    status: Literal["running", "done"]
    metric: str | None
    items: list[CompareItem]


@dataclass
class TuneJob:
    id: str
    status: Literal["running", "done", "stopped", "failed"]
    model: str
    label: str
    progress: tuner.TuneProgress | None = None
    error: str | None = None
    space: list[tuner.SearchParam] = field(default_factory=list)


class CompareRequest(BaseModel):
    models: list[str] = PydanticField(min_length=1, max_length=40)
    preparation: prep.Choices | None = None


class TuneStart(tuner.TuneRequest):
    preparation: prep.Choices | None = None


@dataclass
class TrainingJob:
    id: str
    status: Literal["running", "done", "failed"]
    stage: Stage
    run_id: str | None = None
    error: str | None = None


@dataclass
class ExplanationState:
    status: Literal["running", "done", "failed"]
    error: str | None = None
    explanation: explainer.Explanation | None = None


RUN = TypeAdapter(Run)
EXPLANATION = TypeAdapter(explainer.Explanation)
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
        self._explainer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml-explain")
        self._tuner = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml-tune")
        self._comparisons: OrderedDict[str, CompareJob] = OrderedDict()
        self._tunings: OrderedDict[str, TuneJob] = OrderedDict()
        self._stops: set[str] = set()
        self._explaining: dict[str, Future[explainer.Explanation]] = {}

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

    def catalogue(self, context: catalogue.Context) -> Catalogue:
        """The models that handle a task, their settings with data-dependent defaults, the rules
        between settings, and two or three recommendations for this data."""
        task = context.task
        models = []
        for spec in catalogue.CATALOGUE.values():
            if task not in spec.tasks:
                continue
            settings = spec.settings(context)
            defaults = {s.key: s.default for s in settings}
            models.append(
                ModelView(
                    spec.key,
                    spec.label,
                    spec.family,
                    spec.description,
                    list(spec.tasks),
                    [SettingView(**asdict(setting)) for setting in settings],
                    [RuleView(**asdict(rule)) for rule in spec.rules],
                    spec.badges(context),
                    spec.installed,
                    spec.limit(context),
                    task == "regression" or spec.has_probabilities(defaults),
                    catalogue.spaces.space(spec.key),
                )
            )
        default = evaluate.default_metric(task, context.minority_share)
        metrics = evaluate.metrics_for(task)
        return Catalogue(
            [f for f in catalogue.FAMILIES if any(m.family == f for m in models)],
            models,
            [Recommendation(key, why) for key, why in catalogue.recommend(context)],
            [default, *(m for m in metrics if m != default)],
            default,
            self._compare_default(models, context),
        )

    @staticmethod
    def _compare_default(models: list[ModelView], context: ModelContext) -> list[str]:
        """One model per family that suits the problem and the data."""
        ready = {m.key for m in models if m.installed and m.unavailable is None}
        wanted = [
            catalogue.default_model(context.task),
            "random_forest",
            "xgboost" if "xgboost" in ready else "hist_gradient_boosting",
            "knn",
            "mlp",
            "decision_tree",
        ]
        if context.task != "regression":
            wanted.append("gaussian_nb")
        if context.rows <= 10_000:
            wanted.append("kernel_svm")
        return [key for key in wanted if key in ready]

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
        validation: evaluate.Validation | None = None,
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
            validation or evaluate.Validation(),
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

    def _load(
        self,
        fields: list[Field],
        target: Field,
        source: str,
        limit: int | None = ml_data.MAX_ROWS,
    ) -> tuple[ml_data.Frame, Task]:
        connection = duckdb.connect()
        try:
            frame = ml_data.load(connection, source, fields, target.name, limit)
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
        validation: evaluate.Validation | None = None,
    ) -> None:
        validation = validation or evaluate.Validation()
        try:
            frame, task = self._load(fields, target, source, validation.max_rows)
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
                validation=validation,
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
                " metric, score, seconds, created_at, classes, validation)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                    trained.validation.model_dump_json(),
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
                r["metric"] not in evaluate.LOWER_IS_BETTER,
                spec.label if (spec := catalogue.CATALOGUE.get(r["model"])) else r["model"],
                evaluate.Validation.model_validate_json(r["validation"])
                if r["validation"]
                else evaluate.Validation(),
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

    # --- Comparing models --------------------------------------------------------------------

    def compare(
        self,
        dataset_id: str,
        target: str,
        request: CompareRequest,
        conditions: list[Condition],
        classes: binning.Classes | None = None,
        validation: evaluate.Validation | None = None,
    ) -> CompareJob:
        """Train several models one after the other with the same validation, seed and
        preparation; one failing does not stop the others."""
        unknown = [k for k in request.models if k not in catalogue.CATALOGUE]
        if unknown:
            raise MlError(f"Unknown model(s): {', '.join(unknown)}.", "unknown_model")
        fields, field_, source = self._request(dataset_id, target, None, conditions, classes)
        validation = validation or evaluate.Validation()
        job = CompareJob(
            uuid.uuid4().hex[:12],
            "running",
            validation.metric,
            [CompareItem(k, catalogue.CATALOGUE[k].label) for k in dict.fromkeys(request.models)],
        )
        with self._lock:
            self._comparisons[job.id] = job
            while len(self._comparisons) > KEPT_JOBS:
                self._comparisons.popitem(last=False)

        def run_all() -> None:
            for item in job.items:
                item.status = "running"
                inner = TrainingJob(uuid.uuid4().hex[:12], "running", "loading")
                self._train(
                    inner,
                    dataset_id,
                    fields,
                    field_,
                    item.key,
                    None,
                    source,
                    conditions,
                    request.preparation,
                    classes,
                    validation,
                )
                if inner.status == "done" and inner.run_id:
                    run = self.run(dataset_id, inner.run_id)
                    item.status, item.run_id = "done", inner.run_id
                    item.score, item.seconds = run.score, run.seconds
                    job.metric = run.primary
                else:
                    item.status, item.error = "failed", inner.error
            job.status = "done"

        self._executor.submit(run_all)
        return job

    def comparison(self, job_id: str) -> CompareJob:
        job = self._comparisons.get(job_id)
        if job is None:
            raise MlError("This comparison is no longer followed: open the runs.", "unknown_job")
        return job

    # --- Tuning --------------------------------------------------------------------------------

    def tune(
        self,
        dataset_id: str,
        target: str,
        request: TuneStart,
        conditions: list[Condition],
        classes: binning.Classes | None = None,
        validation: evaluate.Validation | None = None,
    ) -> TuneJob:
        """Search the best settings of a model on the training rows, in the background."""
        fields, field_, source = self._request(
            dataset_id, target, request.model, conditions, classes
        )
        spec = catalogue.CATALOGUE[request.model]
        if not spec.installed:
            raise MlError(f"{spec.label} is not installed in this build.", "not_installed")
        space = request.space if request.space is not None else tuner.default_space(spec.key)
        job = TuneJob(uuid.uuid4().hex[:12], "running", spec.key, spec.label, space=space)
        with self._lock:
            self._tunings[job.id] = job
            while len(self._tunings) > KEPT_JOBS:
                self._tunings.popitem(last=False)
        self._tuner.submit(
            self._tune,
            job,
            dataset_id,
            fields,
            field_,
            source,
            request,
            conditions,
            classes,
            validation or evaluate.Validation(),
        )
        return job

    def _tune(
        self,
        job: TuneJob,
        dataset_id: str,
        fields: list[Field],
        target: Field,
        source: str,
        request: TuneStart,
        conditions: list[Condition],
        classes: binning.Classes | None,
        validation: evaluate.Validation,
    ) -> None:
        try:
            frame, task = self._load(fields, target, source, validation.max_rows)
            if classes is not None:
                task = "binary" if len(classes.names) == 2 else "multiclass"
            setup = trainer._setup(
                frame.data,
                fields,
                target,
                task,
                request.model,
                request.settings,
                None,
                request.preparation,
                classes,
                validation,
            )
            metric = validation.metric or evaluate.default_metric(setup.task, setup.minority)
            job.progress = tuner.TuneProgress(metric, metric not in evaluate.LOWER_IS_BETTER)

            def build(values: dict[str, Any], rows: int) -> Any:
                return trainer.model_pipeline(
                    setup.spec,
                    values,
                    setup.context,
                    setup.preparation,
                    setup.task,
                    rows,
                    setup.unregularized,
                )

            tuner.tune(
                setup.x_train,
                setup.y_train,
                setup.task,
                setup.spec,
                setup.context,
                setup.preparation,
                request.model_copy(update={"space": job.space}),
                metric,
                job.progress,
                lambda: job.id in self._stops,
                build,
            )
            job.status = "stopped" if job.progress.stopped else "done"
            self._save_tuning(dataset_id, target.name, job, request)
        except (
            MlError,
            trainer.TrainingError,
            tuner.TuneError,
            catalogue.SettingsError,
            ValueError,
        ) as error:
            job.status, job.error = "failed", str(error)
        except Exception as error:
            job.status, job.error = "failed", f"Tuning failed: {error}"
        finally:
            self._stops.discard(job.id)

    def _save_tuning(self, dataset_id: str, target: str, job: TuneJob, request: TuneStart) -> None:
        progress = job.progress
        if progress is None:
            return
        with self._db() as connection, connection:
            connection.execute(
                "INSERT INTO ml_tunings (id, dataset_id, target, model, metric, request,"
                " best_value, best_params, default_value, importances, status, seconds, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job.id,
                    dataset_id,
                    target,
                    job.model,
                    progress.metric,
                    request.model_dump_json(),
                    progress.best_value,
                    json.dumps(progress.best_params),
                    progress.default_value,
                    json.dumps(progress.importances),
                    job.status,
                    progress.seconds,
                    _now(),
                ),
            )
            connection.executemany(
                "INSERT INTO ml_trials (tuning_id, number, value, state, params, seconds)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        job.id,
                        t.number,
                        t.value,
                        t.state,
                        json.dumps(t.params, default=str),
                        t.seconds,
                    )
                    for t in progress.trials
                ],
            )

    def tuning(self, job_id: str) -> TuneJob:
        job = self._tunings.get(job_id)
        if job is None:
            raise MlError("This search is no longer followed.", "unknown_job")
        return job

    def stop_tuning(self, job_id: str) -> TuneJob:
        job = self.tuning(job_id)
        if job.status == "running":
            self._stops.add(job_id)
        return job

    # --- Explanations ----------------------------------------------------------------------------

    def explanation(self, dataset_id: str, run_id: str) -> ExplanationState:
        """The run's explanation from the cache, or computed in the background (poll again)."""
        cached = self._folder(dataset_id) / f"{run_id}.explain.json"
        if cached.is_file():
            return ExplanationState(
                "done", explanation=EXPLANATION.validate_json(cached.read_bytes())
            )
        key = f"{dataset_id}/{run_id}"
        with self._lock:
            future = self._explaining.get(key)
            if future is None:
                run = self.run(dataset_id, run_id)
                if not run.evaluation_rows:
                    raise MlError(
                        "This run was trained before explanations existed: train it again to "
                        "explain it.",
                        "no_evaluation_rows",
                    )
                future = self._explainer.submit(self._explain, dataset_id, run)
                self._explaining[key] = future
        if not future.done():
            return ExplanationState("running")
        with self._lock:
            self._explaining.pop(key, None)
        error = future.exception()
        if error is not None:
            message = (
                str(error)
                if isinstance(error, MlError | ValueError)
                else f"Explanation failed: {error}"
            )
            return ExplanationState("failed", message)
        return ExplanationState("done", explanation=future.result())

    def _explain(self, dataset_id: str, run: Run) -> explainer.Explanation:
        folder = self._folder(dataset_id)
        # a file this app wrote itself in its own local workspace, never one received from outside
        pipeline = joblib.load(folder / f"{run.id}.joblib")
        with self._db() as connection:
            row = connection.execute(
                "SELECT conditions FROM ml_runs WHERE id = ?", (run.id,)
            ).fetchone()
        conditions = (
            [Condition.model_validate(c) for c in json.loads(row["conditions"])] if row else []
        )
        fields, target, source = self._request(dataset_id, run.target, None, conditions)
        connection = duckdb.connect()
        try:
            frame = ml_data.load(connection, source, fields, target.name, run.validation.max_rows)
        finally:
            connection.close()
        data = frame.data[frame.data["__row"].isin(list(run.evaluation_rows))].reset_index(
            drop=True
        )
        inputs = [str(c) for c in pipeline.feature_names_in_]
        missing = [c for c in inputs if c not in data.columns]
        if missing or data.empty:
            raise MlError("The data changed since this run: train it again to explain it.")
        series = cast(pd.Series, data[target.name])
        if run.classes is not None:
            y = binning.apply(series, run.classes).astype(str)
        else:
            y = trainer.prepare_target(series, run.task)
        positive = run.classification.positive if run.classification else None
        found = explainer.explain(
            pipeline,
            cast(pd.DataFrame, data[inputs]),
            y,
            data["__row"].to_numpy(dtype=int),
            run.task,
            run.primary,
            [p.row for p in run.predictions],
            positive,
        )
        (folder / f"{run.id}.explain.json").write_bytes(EXPLANATION.dump_json(found))
        return found

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
