import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from app.domain.filters.model import Condition, parse_filters
from app.domain.ml.target import Task
from app.modules.ml.service import (
    MlError,
    MlService,
    ModelView,
    Run,
    RunSummary,
    Targets,
    TrainingJob,
)

router = APIRouter(tags=["module:ml"])


def get_service(request: Request) -> MlService:
    return request.app.state.ml


def active_filters(
    filters: Annotated[str | None, Query(max_length=100_000)] = None,
) -> list[Condition]:
    return parse_filters(filters)


Service = Annotated[MlService, Depends(get_service)]
Filters = Annotated[list[Condition], Depends(active_filters)]


@router.get("/datasets/{dataset_id}/targets")
def targets(dataset_id: str, service: Service, filters: Filters) -> Targets:
    """Every column as a possible target: the problem it defines, or why it cannot be one."""
    return service.targets(dataset_id, filters)


@router.get("/catalog")
def catalog(
    service: Service,
    task: Task,
    rows: Annotated[int, Query(ge=0)] = 1_000,
    minority: Annotated[float | None, Query(ge=0, le=1)] = None,
) -> list[ModelView]:
    """The models that handle a task, with their settings and data-dependent defaults."""
    return service.catalogue(task, rows, minority)


@router.post("/datasets/{dataset_id}/runs", status_code=202)
def train(
    dataset_id: str,
    service: Service,
    filters: Filters,
    target: Annotated[str, Query(min_length=1)],
    model: str | None = None,
    settings: Annotated[str | None, Query(description="JSON object of settings.")] = None,
) -> TrainingJob:
    """Train a model in the background (defaults for everything not given)."""
    try:
        values: dict[str, Any] | None = json.loads(settings) if settings else None
    except json.JSONDecodeError:
        raise MlError("Settings must be a JSON object.", "bad_settings") from None
    if values is not None and not isinstance(values, dict):
        raise MlError("Settings must be a JSON object.", "bad_settings")
    return service.start(dataset_id, target, model, values, filters)


@router.get("/jobs/{job_id}")
def job(job_id: str, service: Service) -> TrainingJob:
    return service.job(job_id)


@router.get("/datasets/{dataset_id}/runs")
def runs(dataset_id: str, service: Service, target: str | None = None) -> list[RunSummary]:
    """Saved runs, most recent first (for one target when given)."""
    return service.runs(dataset_id, target)


@router.get("/datasets/{dataset_id}/runs/{run_id}")
def run(dataset_id: str, run_id: str, service: Service) -> Run:
    return service.run(dataset_id, run_id)


@router.get("/datasets/{dataset_id}/runs/{run_id}/predictions.csv")
def predictions(dataset_id: str, run_id: str, service: Service) -> Response:
    """Predictions on the test rows (sample), as CSV."""
    return Response(
        service.predictions_csv(dataset_id, run_id),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="predictions-{run_id}.csv"'},
    )
