from typing import Annotated

from fastapi import Depends, Request

from app.domain.datasets.service import DatasetService


def get_dataset_service(request: Request) -> DatasetService:
    return request.app.state.datasets


Datasets = Annotated[DatasetService, Depends(get_dataset_service)]
