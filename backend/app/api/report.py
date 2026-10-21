from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, Response

from app.api.filters import Filters
from app.domain.report.service import ReportJob, ReportService

router = APIRouter(tags=["report"])


def get_report_service(request: Request) -> ReportService:
    return request.app.state.reports


Reports = Annotated[ReportService, Depends(get_report_service)]


@router.post("/datasets/{dataset_id}/report", status_code=202)
def start(dataset_id: str, service: Reports, filters: Filters) -> ReportJob:
    """Generate the HTML report of the dataset, over the filtered rows (spec 025)."""
    return service.start(dataset_id, filters)


@router.get("/reports/jobs/{job_id}")
def job(job_id: str, service: Reports) -> ReportJob:
    return service.job(job_id)


@router.delete("/reports/jobs/{job_id}")
def cancel(job_id: str, service: Reports) -> ReportJob:
    return service.cancel(job_id)


@router.get("/reports/jobs/{job_id}/file", response_class=Response)
def download(job_id: str, service: Reports) -> Response:
    name, content = service.file(job_id)
    return Response(
        content,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"},
    )
