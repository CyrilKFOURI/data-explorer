from typing import Annotated

from cyfouri_data_explorer.variable.analyze import VariableProfile
from cyfouri_data_explorer.variable.fitting import Fit
from cyfouri_data_explorer.variable.outliers import OutlierMethod, Outliers
from cyfouri_data_explorer.variable.service import VariableService
from fastapi import APIRouter, Depends, Query, Request

from app.api.filters import Filters

router = APIRouter(tags=["variable"])


def get_variable_service(request: Request) -> VariableService:
    return request.app.state.variable


Variable = Annotated[VariableService, Depends(get_variable_service)]
ColumnName = Annotated[str, Query(min_length=1)]


@router.get("/datasets/{dataset_id}/variable")
def profile(
    dataset_id: str, column: ColumnName, service: Variable, filters: Filters
) -> VariableProfile:
    return service.profile(dataset_id, column, filters)


@router.get("/datasets/{dataset_id}/variable/fit")
def fit(dataset_id: str, column: ColumnName, service: Variable, filters: Filters) -> Fit:
    return service.fit(dataset_id, column, filters)


@router.get("/datasets/{dataset_id}/variable/outliers")
def outliers(
    dataset_id: str,
    column: ColumnName,
    service: Variable,
    filters: Filters,
    method: OutlierMethod = "iqr",
) -> Outliers:
    return service.outliers(dataset_id, column, method, filters)
