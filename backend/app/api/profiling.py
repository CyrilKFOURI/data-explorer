from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.domain.charts.prepare import Chart, ChartParams
from app.domain.profiling.overview import Overview
from app.domain.profiling.service import ProfilingService

router = APIRouter(tags=["profiling"])


def get_profiling_service(request: Request) -> ProfilingService:
    return request.app.state.profiling


Profiling = Annotated[ProfilingService, Depends(get_profiling_service)]


@router.get("/datasets/{dataset_id}/overview")
def overview(dataset_id: str, service: Profiling) -> Overview:
    return service.overview(dataset_id)


@router.get("/datasets/{dataset_id}/columns/chart")
def chart(
    dataset_id: str,
    service: Profiling,
    column: Annotated[str, Query(min_length=1)],
    view: str | None = None,
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
    full: bool = False,
    step: str | None = None,
    bins: Annotated[int | None, Query(ge=5, le=200)] = None,
) -> Chart:
    return service.chart(dataset_id, column, ChartParams(view, top_n, full, step, bins))
