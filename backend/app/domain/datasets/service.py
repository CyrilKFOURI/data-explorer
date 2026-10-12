"""Dataset lifecycle: preview a source, import it in the background, list, rename, delete."""

import shutil
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import duckdb

from app.config import Settings
from app.core import db
from app.core.errors import AppError
from app.core.jobs import JobRunner
from app.core.storage import Workspace
from app.domain.datasets import repository as repo
from app.domain.datasets.repository import DatasetRecord, JobRecord, now
from app.domain.ingestion.browse import Listing, is_within, list_directory
from app.domain.ingestion.errors import IngestionError
from app.domain.ingestion.importer import import_to_parquet
from app.domain.ingestion.options import ImportOptions, SourceOptions
from app.domain.ingestion.preview import ColumnInfo, Preview, preview_source
from app.domain.ingestion.sources import SourceFile, fingerprint, list_source_files
from app.domain.ingestion.sql import lit

SourceState = Literal["ok", "changed", "missing"]


def is_network_path(value: str) -> bool:
    return value.startswith(("\\\\", "//"))


class NotFoundError(AppError):
    def __init__(self, what: str) -> None:
        super().__init__(f"{what} not found", code="not_found", status_code=404)


class DatasetService:
    def __init__(self, workspace: Workspace, settings: Settings, jobs: JobRunner) -> None:
        self.workspace = workspace
        self.settings = settings
        self.jobs = jobs

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        connection = db.connect(self.workspace.db_path)
        try:
            yield connection
        finally:
            connection.close()

    # --- Sources ---------------------------------------------------------------------------

    def allowed_roots(self) -> list[Path] | None:
        if self.settings.data_dir is None:
            return None
        return [self.settings.data_dir, self.workspace.uploads_dir, self.settings.samples_dir]

    def resolve(self, raw_path: str) -> Path:
        path = Path(raw_path).expanduser()
        if is_network_path(raw_path) or is_network_path(path.drive):
            # Opening a network path makes Windows authenticate to a remote host (credential leak).
            raise IngestionError("Network paths are not supported: copy the files locally first.")
        path = path.resolve()
        if is_network_path(path.drive):
            raise IngestionError("Network paths are not supported: copy the files locally first.")
        roots = self.allowed_roots()
        if roots is not None and not is_within(path, [root.resolve() for root in roots]):
            raise IngestionError("This path is outside the allowed data folder.")
        return path

    def browse(self, raw_path: str | None) -> Listing:
        roots = None if self.settings.data_dir is None else [self.settings.data_dir]
        return list_directory(self.resolve(raw_path) if raw_path else None, roots)

    def preview(self, raw_path: str, options: SourceOptions) -> Preview:
        return preview_source(self.resolve(raw_path), options)

    def samples(self) -> list[SourceFile]:
        directory = self.settings.samples_dir
        if not directory.is_dir():
            return []
        try:
            return list_source_files(directory)
        except IngestionError:
            return []

    # --- Import ----------------------------------------------------------------------------

    def start_import(
        self, raw_path: str, name: str | None, options: ImportOptions
    ) -> tuple[DatasetRecord, JobRecord | None]:
        path = self.resolve(raw_path)
        files = list_source_files(path, options.files)
        source_fingerprint = fingerprint(files, options.model_dump(mode="json"))
        with self._db() as connection:
            existing = repo.find_ready_by_fingerprint(connection, source_fingerprint)
            if existing and Path(existing.storage_path).is_file():
                repo.update_dataset(connection, existing.id, last_opened_at=now())
                return self.get(existing.id), None

            dataset_id = uuid.uuid4().hex[:12]
            formats = {file.format for file in files}
            record = DatasetRecord(
                id=dataset_id,
                name=(name or "").strip() or (path.stem if path.is_file() else path.name),
                source_path=str(path),
                source_kind="file" if path.is_file() else "folder",
                format=formats.pop() if len(formats) == 1 else "mixed",
                options=options.model_dump_json(),
                fingerprint=source_fingerprint,
                storage_path=str(self.workspace.dataset_dir(dataset_id) / "data.parquet"),
                status="importing",
                created_at=now(),
                sample_pct=options.sample_pct,
            )
            repo.insert_dataset(connection, record)
            repo.replace_files(connection, dataset_id, files)
            job = self._new_job(connection, dataset_id)
        self.jobs.submit(lambda: self._run_import(record.id, job.id, files, options))
        return record, job

    def reimport(self, dataset_id: str) -> JobRecord:
        record = self.get(dataset_id)
        options = ImportOptions.model_validate_json(record.options)
        path = Path(record.source_path)
        if not path.exists():
            raise IngestionError("The source no longer exists: it can't be reimported.")
        files = list_source_files(path, options.files)
        with self._db() as connection:
            repo.update_dataset(
                connection,
                dataset_id,
                status="importing",
                error=None,
                fingerprint=fingerprint(files, options.model_dump(mode="json")),
            )
            repo.replace_files(connection, dataset_id, files)
            job = self._new_job(connection, dataset_id)
        self.jobs.submit(lambda: self._run_import(dataset_id, job.id, files, options))
        return job

    def _new_job(self, connection: sqlite3.Connection, dataset_id: str) -> JobRecord:
        job = JobRecord(
            id=uuid.uuid4().hex[:12],
            kind="import",
            dataset_id=dataset_id,
            status="pending",
            created_at=now(),
            message="Queued",
        )
        repo.insert_job(connection, job)
        return job

    def _run_import(
        self, dataset_id: str, job_id: str, files: list[SourceFile], options: ImportOptions
    ) -> None:
        with self._db() as connection:
            repo.update_job(connection, job_id, status="running", message="Starting")

            def progress(fraction: float, message: str) -> None:
                repo.update_job(connection, job_id, progress=fraction, message=message)

            target = self.workspace.dataset_dir(dataset_id) / "data.parquet"
            try:
                result = import_to_parquet(files, options, target, progress)
            except Exception as error:
                message = (
                    error.message if isinstance(error, AppError) else f"Import failed: {error}"
                )
                repo.update_dataset(connection, dataset_id, status="error", error=message)
                repo.update_job(
                    connection, job_id, status="failed", message=message, finished_at=now()
                )
                return
            stamp = now()
            repo.update_dataset(
                connection,
                dataset_id,
                status="ready",
                error=None,
                row_count=result.row_count,
                col_count=result.col_count,
                size_bytes=result.size_bytes,
                imported_at=stamp,
                last_opened_at=stamp,
            )
            repo.update_job(
                connection, job_id, status="done", progress=1, message="Done", finished_at=stamp
            )

    # --- Datasets --------------------------------------------------------------------------

    def get(self, dataset_id: str) -> DatasetRecord:
        with self._db() as connection:
            record = repo.get_dataset(connection, dataset_id)
        if record is None:
            raise NotFoundError("Dataset")
        return record

    def list_all(self) -> list[DatasetRecord]:
        with self._db() as connection:
            return repo.list_datasets(connection)

    def latest_job(self, dataset_id: str) -> JobRecord | None:
        with self._db() as connection:
            return repo.latest_job(connection, dataset_id)

    def job(self, job_id: str) -> JobRecord:
        with self._db() as connection:
            job = repo.get_job(connection, job_id)
        if job is None:
            raise NotFoundError("Job")
        return job

    def source_state(self, record: DatasetRecord) -> SourceState:
        with self._db() as connection:
            recorded = repo.list_files(connection, record.id)
        source = Path(record.source_path)
        if not source.exists():
            return "missing"
        for path, size, mtime in recorded:
            file = Path(path)
            if not file.exists():
                return "missing" if record.source_kind == "file" else "changed"
            stat = file.stat()
            if stat.st_size != size or stat.st_mtime != mtime:
                return "changed"
        if record.source_kind == "folder":
            options = ImportOptions.model_validate_json(record.options)
            try:
                current = {str(f.path) for f in list_source_files(source, options.files)}
            except IngestionError:
                return "changed"
            if current != {path for path, _, _ in recorded}:
                return "changed"
        return "ok"

    def rename(self, dataset_id: str, name: str) -> DatasetRecord:
        self.get(dataset_id)
        clean = name.strip()
        if not clean:
            raise AppError("The name can't be empty.", code="invalid_name", status_code=422)
        with self._db() as connection:
            repo.update_dataset(connection, dataset_id, name=clean)
        return self.get(dataset_id)

    def mark_opened(self, dataset_id: str) -> DatasetRecord:
        self.get(dataset_id)
        with self._db() as connection:
            repo.update_dataset(connection, dataset_id, last_opened_at=now())
        return self.get(dataset_id)

    def delete(self, dataset_id: str) -> None:
        record = self.get(dataset_id)
        with self._db() as connection:
            repo.delete_dataset(connection, dataset_id)
            still_used = repo.count_datasets_with_source(connection, record.source_path) > 0
        shutil.rmtree(self.workspace.dataset_dir(dataset_id), ignore_errors=True)
        source = Path(record.source_path)
        uploads = self.workspace.uploads_dir.resolve()
        if not still_used and source.is_relative_to(uploads):
            # Uploaded files are internal copies: remove the upload folder with its dataset.
            shutil.rmtree(uploads / source.relative_to(uploads).parts[0], ignore_errors=True)

    # --- Stored data -----------------------------------------------------------------------

    def _ready_storage(self, dataset_id: str) -> str:
        record = self.get(dataset_id)
        if record.status != "ready":
            raise AppError("This dataset is not ready yet.", code="not_ready", status_code=409)
        return f"read_parquet({lit(record.storage_path)})"

    def schema(self, dataset_id: str) -> list[ColumnInfo]:
        storage = self._ready_storage(dataset_id)
        connection = duckdb.connect()
        try:
            rows = connection.execute(f"DESCRIBE SELECT * FROM {storage}").fetchall()
        finally:
            connection.close()
        return [ColumnInfo(row[0], row[1]) for row in rows]

    def head(self, dataset_id: str, limit: int) -> list[list[str | None]]:
        storage = self._ready_storage(dataset_id)
        connection = duckdb.connect()
        try:
            rows = connection.execute(
                f"SELECT COLUMNS(*)::VARCHAR FROM {storage} LIMIT {int(limit)}"
            ).fetchall()
        finally:
            connection.close()
        return [list(row) for row in rows]

    # --- Uploads ---------------------------------------------------------------------------

    def new_upload_path(self, filename: str) -> Path:
        safe_name = Path(filename).name.strip() or "upload"
        directory = self.workspace.uploads_dir / uuid.uuid4().hex[:12]
        directory.mkdir(parents=True, exist_ok=True)
        return directory / safe_name

    def recover_interrupted(self) -> None:
        with self._db() as connection:
            repo.interrupt_unfinished(connection)
