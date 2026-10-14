from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.filters import Filters
from app.domain.compare.analyze import Comparison
from app.domain.compare.service import CompareService

router = APIRouter(tags=["compare"])


def get_compare_service(request: Request) -> CompareService:
    return request.app.state.compare


Service = Annotated[CompareService, Depends(get_compare_service)]
Name = Annotated[str, Query(min_length=1)]


@router.get("/datasets/{dataset_id}/compare")
def compare(
    dataset_id: str,
    service: Service,
    filters: Filters,
    x: Name,
    y: Name,
    z: Annotated[str | None, Query(min_length=1)] = None,
    color: Annotated[str | None, Query(min_length=1)] = None,
) -> Comparison:
    return service.compare(dataset_id, x, y, z, color, filters)
