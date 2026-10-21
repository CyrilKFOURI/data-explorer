"""What the time-series module lets the AI agent do (spec 026b): read a series (trend,
seasonality, stationarity) and forecast it, through this module's own service."""

from typing import Any, ClassVar, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.core.tools import AppLink, Tool, ToolContext, ToolError, ToolOutput, compact, wait_for
from app.domain.timeseries import series as ts
from app.modules.timeseries.service import Request, TimeSeriesError, TimeSeriesService


class SeriesInput(BaseModel):
    time: str = Field(description="The date or time column.")
    value: str | None = Field(None, description="The number to follow; empty to count rows.")
    period: Literal["auto", "hour", "day", "week", "month", "quarter", "year"] = Field(
        "auto", description="Aggregation step."
    )
    agg: Literal["auto", "sum", "mean", "median", "min", "max", "count"] = Field(
        "auto", description="How values of one period are combined (auto: sum for amounts)."
    )

    def request(self) -> Request:
        return Request(
            time=self.time,
            value=self.value,
            options=ts.Options(period=self.period, aggregate=self.agg),
        )


def _link(args: SeriesInput) -> AppLink:
    params = {"time": args.time} | ({"value": args.value} if args.value else {})
    return AppLink("timeseries", params, "Open in Time series")


def _methods(results: list[Any]) -> list[Any]:
    return [compact(m, max_items=8) for m in results]


class AnalyzeTimeSeries(Tool[SeriesInput]):
    name: ClassVar[str] = "analyze_time_series"
    description: ClassVar[str] = (
        "Read one series over time: its setup (period, aggregation), key figures, trend tests "
        "(Mann-Kendall, Sen's slope), seasonality tests and calendar profile, and stationarity "
        "tests (ADF, KPSS, Phillips-Perron) with the suggested differencing. Use it before a "
        "forecast or to answer 'is it growing / seasonal?'."
    )
    Input: ClassVar[type[BaseModel]] = SeriesInput

    def __init__(self, service: TimeSeriesService) -> None:
        self.service = service

    def label(self, args: SeriesInput) -> str:
        return f"Analysing {args.value or 'rows'} over {args.time}"

    def run(self, ctx: ToolContext, args: SeriesInput) -> ToolOutput:
        request = args.request()
        try:
            overview = self.service.overview(ctx.dataset_id, request, ctx.conditions, None)
            seasonality = self.service.seasonality(ctx.dataset_id, request, ctx.conditions, None)
            stationarity = self.service.stationarity(
                ctx.dataset_id, request, ctx.conditions, "none", None
            )
        except TimeSeriesError as error:
            raise ToolError(error.message) from error
        content = {
            "setup": compact(overview.setup),
            "figures": compact(overview.figures, max_items=8),
            "trend": _methods(overview.methods),
            "seasonality": {
                "detrended_by": seasonality.detrend,
                "methods": _methods(seasonality.methods),
            },
            "stationarity": {
                "synthesis": compact(stationarity.synthesis),
                "suggestion": compact(stationarity.suggestion),
                "methods": _methods(stationarity.methods),
            },
            "notes": [
                m for m in (overview.message, seasonality.message, stationarity.message) if m
            ],
        }
        setup = overview.setup
        summary = f"{len(overview.periods)} periods ({getattr(setup, 'period', '')})"
        return ToolOutput(summary, content, _link(args))


class ForecastInput(SeriesInput):
    horizon: int | None = Field(None, ge=1, le=500, description="Periods ahead; empty: automatic.")


class Forecast(Tool[ForecastInput]):
    name: ClassVar[str] = "forecast"
    kind = "compute"
    description: ClassVar[str] = (
        "Forecast a series: baseline (naive, seasonal naive) and statistical models (ETS, auto "
        "ARIMA) scored by rolling-origin validation, the best refitted with prediction "
        "intervals. Needs at least 10 periods. Analyse the series first."
    )
    Input: ClassVar[type[BaseModel]] = ForecastInput

    def __init__(self, service: TimeSeriesService) -> None:
        self.service = service

    def label(self, args: ForecastInput) -> str:
        return f"Forecasting {args.value or 'rows'}"

    def run(self, ctx: ToolContext, args: ForecastInput) -> ToolOutput:
        try:
            job = self.service.start_forecast(
                ctx.dataset_id, args.request(), ctx.conditions, args.horizon
            )
        except TimeSeriesError as error:
            raise ToolError(error.message) from error
        forecasts = self.service.forecasts

        def poll() -> Any:
            found = forecasts.get(job.id)
            if found is None:
                raise ToolError("The forecast is no longer available: run it again.")
            return found

        job = wait_for(
            poll,
            lambda j: j.status != "running",
            ctx,
            describe=lambda j: (
                f"Model {j.done + 1} of {j.total}: {j.current or ''}",
                j.done / max(j.total, 1),
            ),
            cancel=lambda: forecasts.cancel(job.id),
        )
        if job.result is None:
            raise ToolError(f"Forecast {job.status}: {job.error or 'no result'}")
        content = compact(job.result, max_items=12)
        return ToolOutput("Forecast ready", content, _link(args))


def agent_tools(app: FastAPI) -> list[Tool[Any]]:
    service: TimeSeriesService = app.state.timeseries
    return [AnalyzeTimeSeries(service), Forecast(service)]
