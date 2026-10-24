from typing import Annotated, Literal

from cyfouri_data_explorer.filters.model import Condition, parse_filters
from cyfouri_data_explorer.timeseries import autocorrelation as ac
from cyfouri_data_explorer.timeseries import breaks as br
from cyfouri_data_explorer.timeseries import forecast as fc
from cyfouri_data_explorer.timeseries import methods
from cyfouri_data_explorer.timeseries import residuals as rs
from cyfouri_data_explorer.timeseries import stationarity as st
from cyfouri_data_explorer.timeseries import volatility as vo
from cyfouri_data_explorer.timeseries.decomposition import Method
from cyfouri_data_explorer.timeseries.forecasting import ForecastJob
from cyfouri_data_explorer.timeseries.series import Aggregate, Align, Gaps, Options, Period
from cyfouri_data_explorer.timeseries.service import Request as SeriesRequest
from cyfouri_data_explorer.timeseries.service import (
    SeriesAutocorrelation,
    SeriesBreaks,
    SeriesDecomposition,
    SeriesOverview,
    SeriesResiduals,
    SeriesSeasonality,
    SeriesStationarity,
    SeriesVolatility,
    TimeSeriesError,
    TimeSeriesService,
)
from fastapi import APIRouter, Depends, Query, Request

router = APIRouter(tags=["module:timeseries"])

Name = Annotated[str | None, Query(min_length=1)]


def get_service(request: Request) -> TimeSeriesService:
    return request.app.state.timeseries


def active_filters(
    filters: Annotated[str | None, Query(max_length=100_000)] = None,
) -> list[Condition]:
    return parse_filters(filters)


def series_request(
    time: Name = None,
    value: Name = None,
    group: Name = None,
    series: Annotated[str | None, Query()] = None,
    period: Period | Literal["auto"] = "auto",
    agg: Aggregate | Literal["auto"] = "auto",
    window: Annotated[int | None, Query(ge=2, le=365)] = None,
    align: Align = "trailing",
    gaps: Gaps = "leave",
    season: Annotated[int | None, Query(ge=2, le=400)] = None,
) -> SeriesRequest:
    return SeriesRequest(
        time, value, group, series, Options(period, agg, window, align), gaps, season
    )


def chosen_methods(text: str | None, catalogue: dict) -> list[str] | None:
    if not text:
        return None
    keys = [key.strip() for key in text.split(",") if key.strip()]
    unknown = [key for key in keys if key not in catalogue]
    if unknown:
        raise TimeSeriesError(f"Unknown method(s): {', '.join(unknown)}.", "unknown_method")
    return keys


Service = Annotated[TimeSeriesService, Depends(get_service)]
Series = Annotated[SeriesRequest, Depends(series_request)]
Filters = Annotated[list[Condition], Depends(active_filters)]
Methods = Annotated[str | None, Query(alias="methods", description="Comma-separated method keys.")]


@router.get("/datasets/{dataset_id}/overview")
def overview(
    dataset_id: str, service: Service, request: Series, filters: Filters, methods_: Methods = None
) -> SeriesOverview:
    """The series, its rolling statistics, key figures and trend methods."""
    return service.overview(dataset_id, request, filters, chosen_methods(methods_, methods.TREND))


@router.get("/datasets/{dataset_id}/seasonality")
def seasonality(
    dataset_id: str, service: Service, request: Series, filters: Filters, methods_: Methods = None
) -> SeriesSeasonality:
    """Calendar profiles, one line per year, and seasonality methods."""
    keys = chosen_methods(methods_, methods.SEASONALITY)
    return service.seasonality(dataset_id, request, filters, keys)


@router.get("/datasets/{dataset_id}/stationarity")
def stationarity(
    dataset_id: str,
    service: Service,
    request: Series,
    filters: Filters,
    transform: st.Transform = "none",
    methods_: Methods = None,
) -> SeriesStationarity:
    """Unit-root and stationarity tests on the series or a transformation of it."""
    keys = chosen_methods(methods_, st.STATIONARITY)
    return service.stationarity(dataset_id, request, filters, transform, keys)


@router.get("/datasets/{dataset_id}/autocorrelation")
def autocorrelation(
    dataset_id: str,
    service: Service,
    request: Series,
    filters: Filters,
    transform: st.Transform = "none",
    methods_: Methods = None,
    pacf: ac.PacfMethod = "ywm",
    ar: Annotated[int | None, Query(ge=1, le=24, description="AR order (default: by AIC).")] = None,
) -> SeriesAutocorrelation:
    """ACF, PACF, a reading of their shapes, and autocorrelation / randomness tests."""
    keys = chosen_methods(methods_, ac.AUTOCORRELATION)
    return service.autocorrelation(dataset_id, request, filters, transform, keys, pacf, ar)


@router.get("/datasets/{dataset_id}/volatility")
def volatility(
    dataset_id: str,
    service: Service,
    request: Series,
    filters: Filters,
    methods_: Methods = None,
    spread: Annotated[int | None, Query(ge=2, le=365, description="Rolling window.")] = None,
) -> SeriesVolatility:
    """Rolling spread of the residuals and heteroscedasticity / ARCH tests."""
    keys = chosen_methods(methods_, vo.VOLATILITY)
    return service.volatility(dataset_id, request, filters, keys, spread)


@router.get("/datasets/{dataset_id}/residuals")
def residuals(
    dataset_id: str,
    service: Service,
    request: Series,
    filters: Filters,
    source: rs.Source = "residuals",
) -> SeriesResiduals:
    """Distribution of the residuals, the series or its returns: statistics, normality, laws."""
    return service.residuals(dataset_id, request, filters, source)


@router.get("/datasets/{dataset_id}/breaks")
def breaks(
    dataset_id: str,
    service: Service,
    request: Series,
    filters: Filters,
    search: br.Search = "pelt",
    cost: br.Cost | Literal["auto"] = "auto",
    sensitivity: br.Sensitivity = "medium",
    methods_: Methods = None,
    anomaly: br.Anomaly = "robust_z",
    threshold: Annotated[float, Query(ge=2, le=6)] = 3.5,
) -> SeriesBreaks:
    """Change points, single-break tests and anomalies."""
    keys = chosen_methods(methods_, br.BREAK_TESTS)
    return service.breaks(
        dataset_id, request, filters, search, cost, sensitivity, keys, anomaly, threshold
    )


def _orders(text: str, name: str) -> tuple[int, int, int]:
    try:
        values = tuple(int(part) for part in text.split(","))
    except ValueError:
        values = ()
    if len(values) != 3 or not all(0 <= v <= 3 for v in values):
        raise TimeSeriesError(
            f"{name} must be three integers from 0 to 3, like 1,1,1.", "bad_order"
        )
    return values  # type: ignore[return-value]


@router.post("/datasets/{dataset_id}/forecast", status_code=202)
def start_forecast(
    dataset_id: str,
    service: Service,
    request: Series,
    filters: Filters,
    horizon: Annotated[int | None, Query(ge=1, le=500)] = None,
    methods_: Methods = None,
    order: str = "1,1,1",
    sorder: str = "0,0,0",
) -> ForecastJob:
    """Start (or reuse) a forecast job: models scored by rolling origin, then refitted."""
    keys = chosen_methods(methods_, fc.MODELS)
    return service.start_forecast(
        dataset_id,
        request,
        filters,
        horizon,
        keys,
        _orders(order, "order"),
        _orders(sorder, "seasonal order"),
    )


def _job(service: TimeSeriesService, job_id: str) -> ForecastJob:
    job = service.forecasts.get(job_id)
    if job is None:
        raise TimeSeriesError("This forecast is no longer available: run it again.", "unknown_job")
    return job


@router.get("/forecast-jobs/{job_id}")
def forecast_job(job_id: str, service: Service) -> ForecastJob:
    """Progress, then the result, of a forecast job."""
    return _job(service, job_id)


@router.delete("/forecast-jobs/{job_id}")
def cancel_forecast(job_id: str, service: Service) -> ForecastJob:
    """Stop a forecast after the model being fitted."""
    _job(service, job_id)
    return service.forecasts.cancel(job_id)  # type: ignore[return-value]


@router.get("/datasets/{dataset_id}/decomposition")
def decomposition(
    dataset_id: str, service: Service, request: Series, filters: Filters, method: Method = "stl"
) -> SeriesDecomposition:
    """Trend, seasonal and remainder components."""
    return service.decomposition(dataset_id, request, filters, method)
