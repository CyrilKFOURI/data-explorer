"""Synthetic data page: plan, generation jobs, saved runs, on-demand evaluations, new dataset."""

import io
import json
import re
import shutil
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

import duckdb
import pandas as pd
from pydantic import BaseModel, Field, TypeAdapter

from app.core import db
from app.core.errors import AppError
from app.core.storage import Workspace
from app.domain.columns.service import ColumnChange, ColumnService, ColumnView
from app.domain.filters.scope import scoped_source, where_for
from app.domain.ingestion.options import ImportOptions
from app.domain.ml.data import Field as TypedField
from app.domain.ml.data import _expression
from app.domain.synthetic import compare as side_by_side
from app.domain.synthetic import plan
from app.domain.synthetic.generate import Spec, group_like, synthesize
from app.domain.synthetic.methods import Cancelled, Options
from app.domain.synthetic.plan import Method, Plan, PlanColumn, Treatment
from app.domain.synthetic.privacy import Disclosure, PrivacyError, disclosure
from app.domain.synthetic.report import LeftOut, Report, evaluate
from app.domain.synthetic.utility import Utility, UtilityError, utility

Stage = Literal["loading", "generating", "evaluating", "saving"]
KEPT_JOBS = 32
HOLDOUT_SHARE = 5  # 1 row in 5 is held out
MAX_HOLDOUT = 20_000
PREVIEW_ROWS = 100
FRAMES_CACHE = 2


class SyntheticError(AppError):
    def __init__(self, message: str, code: str = "synthetic", status_code: int = 422) -> None:
        super().__init__(message, code=code, status_code=status_code)


class Bound(BaseModel):
    minimum: float | None = None
    maximum: float | None = None


class RunRequest(BaseModel):
    """Everything not given takes the plan's automatic choice."""

    method: Method = "cart"
    rows: int | None = Field(default=None, ge=plan.MIN_GENERATED, le=plan.MAX_GENERATED)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    smooth: bool = True  # CART: keeps synthetic numbers off the real values (fewer copies)
    drop_copies: bool = True  # replace synthetic rows identical to a real one
    treatments: dict[str, Treatment] = Field(default_factory=dict)
    bounds: dict[str, Bound] = Field(default_factory=dict)


@dataclass
class SyntheticJob:
    id: str
    status: Literal["running", "done", "failed", "cancelled"]
    stage: Stage
    run_id: str | None = None
    error: str | None = None


@dataclass
class RunColumn:
    name: str
    type: str
    treatment: Treatment


@dataclass
class SyntheticRun:
    id: str
    dataset_id: str
    created_at: str
    method: Method
    method_label: str
    settings: RunRequest
    rows: int
    seconds: float
    train_rows: int
    holdout_rows: int
    columns: list[RunColumn]
    report: Report
    created_dataset_id: str | None = None


@dataclass
class SyntheticRunSummary:
    id: str
    method: Method
    method_label: str
    rows: int
    seconds: float
    created_at: str
    scores: dict[str, float | None]
    created_dataset_id: str | None = None
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyntheticPreview:
    columns: list[str]
    rows: list[list[str | None]]
    total: int


@dataclass
class Origin:
    """A dataset created from a synthetic run."""

    source_id: str
    source_name: str
    run_id: str


RUN = TypeAdapter(SyntheticRun)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip() or "synthetic"


class SyntheticService:
    def __init__(self, columns: ColumnService, workspace: Workspace) -> None:
        self.columns = columns
        self.workspace = workspace
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="synthetic")
        self._jobs: OrderedDict[str, SyntheticJob] = OrderedDict()
        self._stops: set[str] = set()
        self._lock = threading.Lock()
        self._frames: OrderedDict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]] = (
            OrderedDict()
        )
        self._pending: dict[str, list[ColumnChange]] = {}  # imported file → column types to copy

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.workspace.db_path)
        try:
            yield connection
        finally:
            connection.close()

    def _folder(self, dataset_id: str, run_id: str) -> Path:
        return self.workspace.dataset_dir(dataset_id) / "synthetic" / run_id

    # --- Plan ----------------------------------------------------------------------------------

    def _views(self, dataset_id: str) -> tuple[str, list[ColumnView]]:
        dataset = self.columns.ready(dataset_id)
        return dataset.storage_path, self.columns.columns(dataset_id)

    def plan(self, dataset_id: str) -> Plan:
        storage, views = self._views(dataset_id)
        source = scoped_source(storage, where_for(views, []))
        fields = [TypedField(v.name, v.type, v.parser, v.role, v.order) for v in views]
        parts = ", ".join(
            f"count({_expression(f)}), count(DISTINCT {_expression(f)})" for f in fields
        )
        connection = duckdb.connect()
        try:
            row = connection.execute(f"SELECT count(*), {parts} FROM {source}").fetchone() or ()
        finally:
            connection.close()
        rows = int(row[0]) if row else 0
        columns = [
            PlanColumn(
                v.name, v.type, v.role, rows, int(row[1 + 2 * i]), int(row[2 + 2 * i]), v.excluded
            )
            for i, v in enumerate(views)
        ]
        return plan.make_plan(columns, rows)

    def _specs(
        self, dataset_id: str, request: RunRequest
    ) -> tuple[Plan, list[Spec], list[LeftOut]]:
        found = self.plan(dataset_id)
        if found.error:
            raise SyntheticError(found.error, "cannot_generate")
        names = {c.name for c in found.columns}
        unknown = [n for n in [*request.treatments, *request.bounds] if n not in names]
        if unknown:
            raise SyntheticError(f"Unknown column(s): {', '.join(unknown)}.", "unknown_column")
        _, views = self._views(dataset_id)
        orders = {v.name: v.order for v in views}
        specs, left_out = [], []
        for column in found.columns:
            treatment = request.treatments.get(column.name, column.treatment)
            if treatment != column.treatment and treatment not in column.options:
                raise SyntheticError(
                    f"{column.name!r} cannot be set to {treatment!r} ({column.reason})",
                    "bad_treatment",
                )
            if treatment == "leave":
                left_out.append(LeftOut(column.name, column.reason))
                continue
            bound = request.bounds.get(column.name, Bound())
            specs.append(
                Spec(
                    column.name,
                    column.type,
                    treatment,
                    orders.get(column.name),
                    column.grouped,
                    bound.minimum,
                    bound.maximum,
                )
            )
        if not any(s.treatment == "model" for s in specs):
            raise SyntheticError("Model at least one column.", "nothing_to_model")
        return found, specs, left_out

    # --- Generation ----------------------------------------------------------------------------

    def start(self, dataset_id: str, request: RunRequest) -> SyntheticJob:
        found, specs, left_out = self._specs(dataset_id, request)
        rows = request.rows or found.default_rows
        job = SyntheticJob(uuid.uuid4().hex[:12], "running", "loading")
        with self._lock:
            self._jobs[job.id] = job
            while len(self._jobs) > KEPT_JOBS:
                self._jobs.popitem(last=False)
        self._executor.submit(self._run, job, dataset_id, request, specs, left_out, rows)
        return job

    def job(self, job_id: str) -> SyntheticJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise SyntheticError(
                "This generation is no longer followed: open the runs.", "unknown_job", 404
            )
        return job

    def cancel(self, job_id: str) -> SyntheticJob:
        job = self.job(job_id)
        if job.status == "running":
            self._stops.add(job_id)
        return job

    def _load(
        self, dataset_id: str, specs: list[Spec], seed: int
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, pd.Series]]:
        """Training and held-out real rows (typed), and every real value of the columns that are
        regenerated or faked (so none is reused)."""
        storage, views = self._views(dataset_id)
        by_name = {v.name: v for v in views}
        fields = [
            TypedField(
                s.name,
                by_name[s.name].type,
                by_name[s.name].parser,
                by_name[s.name].role,
                by_name[s.name].order,
            )
            for s in specs
        ]
        source = scoped_source(storage, where_for(views, []), numbered=True)
        selected = ", ".join(f"{_expression(f)} AS c{i}" for i, f in enumerate(fields))
        relation = f"(SELECT {selected}, hash(file_row_number + {int(seed)}) AS __h FROM {source})"
        connection = duckdb.connect()
        try:
            train = connection.execute(
                f"SELECT * EXCLUDE (__h) FROM {relation} WHERE __h % {HOLDOUT_SHARE} <> 0 "
                f"ORDER BY __h LIMIT {plan.MAX_TRAIN_ROWS}"
            ).df()
            holdout = connection.execute(
                f"SELECT * EXCLUDE (__h) FROM {relation} WHERE __h % {HOLDOUT_SHARE} = 0 "
                f"ORDER BY __h LIMIT {MAX_HOLDOUT}"
            ).df()
            existing = {}
            for i, spec in enumerate(specs):
                if spec.treatment in ("unique", "fake"):
                    existing[spec.name] = (
                        connection.execute(
                            f"SELECT DISTINCT {_expression(fields[i])} FROM {source}"
                        )
                        .df()
                        .iloc[:, 0]
                    )
        finally:
            connection.close()
        names = [s.name for s in specs]
        train.columns, holdout.columns = names, names
        return self._typed(train, specs), self._typed(holdout, specs), existing

    @staticmethod
    def _typed(frame: pd.DataFrame, specs: list[Spec]) -> pd.DataFrame:
        for spec in specs:
            if spec.treatment == "model" and spec.type in plan.NUMERIC:
                frame[spec.name] = cast(
                    pd.Series, pd.to_numeric(frame[spec.name], errors="coerce")
                ).astype(float)
        return frame

    def _run(
        self,
        job: SyntheticJob,
        dataset_id: str,
        request: RunRequest,
        specs: list[Spec],
        left_out: list[LeftOut],
        rows: int,
    ) -> None:
        started = time.perf_counter()

        def stopped() -> bool:
            return job.id in self._stops

        try:
            train, holdout, existing = self._load(dataset_id, specs, request.seed)
            if len(train) < plan.MIN_ROWS // 2:
                raise SyntheticError("Too few rows to learn from.")
            if stopped():
                raise Cancelled
            job.stage = "generating"
            options = Options(
                rows=rows, seed=request.seed, smooth=request.smooth, drop_copies=request.drop_copies
            )
            synthesis = synthesize(train, specs, request.method, options, existing, stopped)
            if stopped():
                raise Cancelled
            job.stage = "evaluating"
            train, holdout = synthesis.train, group_like(holdout, synthesis.learned)
            unique = [s.name for s in specs if s.treatment == "unique"]
            report = evaluate(
                train,
                holdout,
                synthesis.frame,
                synthesis.learned,
                synthesis.fitted,
                unique,
                synthesis.bounds,
                left_out,
                request.seed,
                stopped,
            )
            if stopped():
                raise Cancelled
            job.stage = "saving"
            run = SyntheticRun(
                uuid.uuid4().hex[:12],
                dataset_id,
                _now(),
                request.method,
                plan.METHODS[request.method][0],
                request,
                rows,
                round(time.perf_counter() - started, 2),
                len(train),
                len(holdout),
                [RunColumn(s.name, s.type, s.treatment) for s in specs],
                report,
            )
            self._save(run, train, holdout, synthesis.frame)
            job.run_id, job.status = run.id, "done"
        except Cancelled:
            job.status, job.error = "cancelled", "Stopped: nothing was saved."
        except (SyntheticError, ValueError) as error:
            job.status, job.error = "failed", str(error)
        except Exception as error:
            job.status, job.error = "failed", f"Generation failed: {error}"
        finally:
            self._stops.discard(job.id)

    def _save(
        self, run: SyntheticRun, train: pd.DataFrame, holdout: pd.DataFrame, data: pd.DataFrame
    ) -> None:
        folder = self._folder(run.dataset_id, run.id)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            self._export(data, run).to_parquet(folder / "data.parquet", index=False)
            train.to_parquet(folder / "train.parquet", index=False)
            holdout.to_parquet(folder / "holdout.parquet", index=False)
            (folder / "report.json").write_bytes(RUN.dump_json(run))
            with self._db() as connection, connection:
                connection.execute(
                    "INSERT INTO synthetic_runs (id, dataset_id, method, settings, rows, scores,"
                    " status, seconds, created_at) VALUES (?, ?, ?, ?, ?, ?, 'done', ?, ?)",
                    (
                        run.id,
                        run.dataset_id,
                        run.method,
                        run.settings.model_dump_json(),
                        run.rows,
                        json.dumps(self._scores(run)),
                        run.seconds,
                        run.created_at,
                    ),
                )
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise

    @staticmethod
    def _scores(run: SyntheticRun) -> dict[str, float | None]:
        scores = run.report.scores
        return {
            "diagnostic": scores.diagnostic,
            "quality": scores.quality,
            "shapes": scores.shapes,
            "trends": scores.trends,
            "detection": scores.detection,
            "privacy": scores.privacy,
            "utility": scores.utility,
        }

    @staticmethod
    def _export(data: pd.DataFrame, run: SyntheticRun) -> pd.DataFrame:
        """Typed values as a dataset stores them: booleans and whole numbers as such."""
        out = data.copy()
        for column in run.columns:
            if column.treatment != "model":
                continue
            if column.type == "boolean":
                out[column.name] = (
                    out[column.name].map({"True": True, "False": False}.get).astype("boolean")
                )
            elif column.type == "numeric_discrete":
                out[column.name] = out[column.name].round().astype("Int64")
        return out

    # --- Runs ----------------------------------------------------------------------------------

    def runs(self, dataset_id: str) -> list[SyntheticRunSummary]:
        self.columns.datasets.get(dataset_id)
        with self._db() as connection:
            rows = connection.execute(
                "SELECT * FROM synthetic_runs WHERE dataset_id = ? ORDER BY created_at DESC",
                (dataset_id,),
            ).fetchall()
        return [self._summary(r) for r in rows]

    @staticmethod
    def _summary(row: sqlite3.Row) -> SyntheticRunSummary:
        method = row["method"]
        return SyntheticRunSummary(
            row["id"],
            method,
            plan.METHODS[method][0] if method in plan.METHODS else method,
            row["rows"],
            row["seconds"],
            row["created_at"],
            json.loads(row["scores"]) if row["scores"] else {},
            row["created_dataset_id"],
            json.loads(row["settings"]),
        )

    def run(self, dataset_id: str, run_id: str) -> SyntheticRun:
        path = self._folder(dataset_id, run_id) / "report.json"
        if not path.is_file():
            raise SyntheticError("Unknown run.", "unknown_run", 404)
        run = RUN.validate_json(path.read_bytes())
        with self._db() as connection:
            row = connection.execute(
                "SELECT created_dataset_id FROM synthetic_runs WHERE id = ?", (run_id,)
            ).fetchone()
        run.created_dataset_id = row["created_dataset_id"] if row else None
        return run

    def compare(self, dataset_id: str, run_ids: list[str]) -> list[SyntheticRunSummary]:
        if not 2 <= len(run_ids) <= 5:
            raise SyntheticError("Pick 2 to 5 runs to compare.", "bad_compare")
        found = {r.id: r for r in self.runs(dataset_id)}
        missing = [i for i in run_ids if i not in found]
        if missing:
            raise SyntheticError(f"Unknown run(s): {', '.join(missing)}.", "unknown_run", 404)
        return [found[i] for i in run_ids]

    def delete(self, dataset_id: str, run_id: str) -> None:
        self.run(dataset_id, run_id)
        with self._db() as connection, connection:
            connection.execute("DELETE FROM synthetic_runs WHERE id = ?", (run_id,))
        self._frames.pop(run_id, None)
        shutil.rmtree(self._folder(dataset_id, run_id), ignore_errors=True)

    def _frames_of(
        self, dataset_id: str, run_id: str
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """(training rows, held-out rows, synthetic rows), typed as the evaluation saw them."""
        if run_id in self._frames:
            self._frames.move_to_end(run_id)
            return self._frames[run_id]
        run = self.run(dataset_id, run_id)
        folder = self._folder(dataset_id, run_id)
        train = pd.read_parquet(folder / "train.parquet")
        holdout = pd.read_parquet(folder / "holdout.parquet")
        data = pd.read_parquet(folder / "data.parquet")
        for column in run.columns:
            if column.type == "boolean" and column.treatment == "model":
                data[column.name] = data[column.name].map(
                    lambda v: None if pd.isna(v) else ("True" if v else "False")
                )
            elif column.type == "numeric_discrete" and column.treatment == "model":
                data[column.name] = data[column.name].astype(float)
        frames = (train, holdout, data)
        self._frames[run_id] = frames
        while len(self._frames) > FRAMES_CACHE:
            self._frames.popitem(last=False)
        return frames

    def preview(self, dataset_id: str, run_id: str) -> SyntheticPreview:
        _, _, data = self._frames_of(dataset_id, run_id)
        head = data.head(PREVIEW_ROWS)
        rows = [
            [None if pd.isna(v) else str(v).replace(" 00:00:00", "") for v in record]
            for record in head.itertuples(index=False)
        ]
        return SyntheticPreview(list(data.columns), rows, len(data))

    def download(self, dataset_id: str, run_id: str, kind: Literal["csv", "parquet"]) -> bytes:
        self.run(dataset_id, run_id)
        path = self._folder(dataset_id, run_id) / "data.parquet"
        if kind == "parquet":
            return path.read_bytes()
        buffer = io.StringIO()
        pd.read_parquet(path).to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8")

    # --- On-demand evaluations -----------------------------------------------------------------

    def _rewrite(self, run: SyntheticRun) -> None:
        (self._folder(run.dataset_id, run.id) / "report.json").write_bytes(RUN.dump_json(run))
        with self._db() as connection, connection:
            connection.execute(
                "UPDATE synthetic_runs SET scores = ? WHERE id = ?",
                (json.dumps(self._scores(run)), run.id),
            )

    def utility(self, dataset_id: str, run_id: str, target: str) -> Utility:
        run = self.run(dataset_id, run_id)
        train, holdout, data = self._frames_of(dataset_id, run_id)
        try:
            found = utility(train, data, holdout, run.report.learned, target, run.settings.seed)
        except UtilityError as error:
            raise SyntheticError(str(error), "bad_target") from None
        run.report.utility = found
        run.report.scores.utility = found.ratio
        self._rewrite(run)
        return found

    def disclosure(
        self, dataset_id: str, run_id: str, known: list[str], sensitive: str
    ) -> Disclosure:
        run = self.run(dataset_id, run_id)
        train, _, data = self._frames_of(dataset_id, run_id)
        try:
            found = disclosure(train, data, run.report.learned, known, sensitive, run.settings.seed)
        except PrivacyError as error:
            raise SyntheticError(str(error), "bad_disclosure") from None
        run.report.disclosure = found
        self._rewrite(run)
        return found

    def _learned(self, run: SyntheticRun, name: str):
        item = next((i for i in run.report.learned if i.name == name), None)
        if item is None:
            raise SyntheticError(
                f"{name!r} is not a modelled column of this run.", "unknown_column", 404
            )
        return item

    def column(
        self, dataset_id: str, run_id: str, column: str, bins: int | None, target: str | None
    ) -> side_by_side.ColumnDetail:
        run = self.run(dataset_id, run_id)
        item = self._learned(run, column)
        target_item = self._learned(run, target) if target else None
        train, _, data = self._frames_of(dataset_id, run_id)
        score = next((s.score for s in run.report.quality.shape_scores if s.column == column), None)
        real = train.sample(min(len(train), 20_000), random_state=run.settings.seed)
        fake = data.sample(min(len(data), 20_000), random_state=run.settings.seed)
        return side_by_side.column_detail(real, fake, item, score, bins, target_item)

    def pair(self, dataset_id: str, run_id: str, a: str, b: str) -> side_by_side.PairDetail:
        run = self.run(dataset_id, run_id)
        first, second = self._learned(run, a), self._learned(run, b)
        if a == b:
            raise SyntheticError("Pick two different columns.", "same_column")
        train, _, data = self._frames_of(dataset_id, run_id)
        return side_by_side.pair_detail(train, data, first, second, run.settings.seed)

    # --- New dataset ---------------------------------------------------------------------------

    def create_dataset(self, dataset_id: str, run_id: str) -> str:
        """Import the synthetic rows as a new dataset, with the source's column types."""
        run = self.run(dataset_id, run_id)
        datasets = self.columns.datasets
        if run.created_dataset_id:
            try:
                datasets.get(run.created_dataset_id)
                return run.created_dataset_id
            except AppError:
                pass
        source = datasets.get(dataset_id)
        name = f"{source.name} (synthetic)"
        target = datasets.new_upload_path(f"{_safe_name(name)}.parquet")
        shutil.copyfile(self._folder(dataset_id, run_id) / "data.parquet", target)
        views = {v.name: v for v in self.columns.columns(dataset_id)}
        self._pending[str(datasets.resolve(str(target)))] = [
            ColumnChange(
                name=c.name,
                type=views[c.name].type,
                role=views[c.name].role or "",
                order=views[c.name].order or [],
            )
            for c in run.columns
            if c.name in views
        ]
        record, _ = datasets.start_import(str(target), name, ImportOptions())
        with self._db() as connection, connection:
            connection.execute(
                "UPDATE synthetic_runs SET created_dataset_id = ? WHERE id = ?", (record.id, run_id)
            )
        return record.id

    def after_import(self, dataset_id: str, storage_path: str) -> None:
        """Import step: a dataset made from a run gets the source's types, roles and orders."""
        record = self.columns.datasets.get(dataset_id)
        changes = self._pending.pop(record.source_path, None)
        if changes:
            self.columns.apply(dataset_id, storage_path, changes)

    def origin(self, dataset_id: str) -> Origin | None:
        with self._db() as connection:
            row = connection.execute(
                "SELECT r.id, r.dataset_id, d.name FROM synthetic_runs r"
                " JOIN datasets d ON d.id = r.dataset_id WHERE r.created_dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        return Origin(row["dataset_id"], row["name"], row["id"]) if row else None
