from fastapi import APIRouter

from app.api.deps import Datasets
from app.schemas.datasets import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job(job_id: str, service: Datasets) -> JobOut:
    return JobOut.of(service.job(job_id))
