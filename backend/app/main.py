"""FastAPI application: API under /api/v1, built frontend served in production."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import columns, datasets, health, jobs, profiling, sources, variable
from app.api.errors import register_error_handlers
from app.api.security import protect
from app.config import Settings
from app.core import db
from app.core.jobs import JobRunner, ThreadJobRunner
from app.core.storage import Workspace
from app.domain.columns.service import ColumnService
from app.domain.datasets.service import DatasetService
from app.domain.profiling.service import ProfilingService
from app.domain.variable.service import VariableService
from app.modules.registry import mount_modules

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None, job_runner: JobRunner | None = None) -> FastAPI:
    settings = settings or Settings()
    workspace = Workspace(settings.home)
    runner = job_runner or ThreadJobRunner()
    dataset_service = DatasetService(workspace, settings, runner)
    column_service = ColumnService(workspace, dataset_service)
    dataset_service.after_import.append(column_service.detect_storage)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        workspace.ensure()
        connection = db.connect(workspace.db_path)
        try:
            db.apply_migrations(connection)
        finally:
            connection.close()
        dataset_service.recover_interrupted()
        yield
        runner.shutdown()

    app = FastAPI(title="Data Explorer", version=health.app_version(), lifespan=lifespan)
    app.state.workspace = workspace
    app.state.datasets = dataset_service
    app.state.columns = column_service
    app.state.profiling = ProfilingService(column_service)
    app.state.variable = VariableService(column_service)
    register_error_handlers(app)
    protect(app, tuple(settings.allowed_hosts))

    api = APIRouter(prefix=API_PREFIX)
    for module in (health, datasets, sources, jobs, columns, profiling, variable):
        api.include_router(module.router)
    app.include_router(api)
    mount_modules(app, API_PREFIX)

    if settings.static_dir and settings.static_dir.is_dir():
        serve_frontend(app, settings.static_dir)
    return app


def serve_frontend(app: FastAPI, static_dir: Path) -> None:
    """Serve the built single-page app; unknown non-API paths fall back to index.html."""
    root = static_dir.resolve()
    if (root / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = (root / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(root / "index.html")


app = create_app()
