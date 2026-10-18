"""Time series page: one series of a dataset, read through the active filters, then analysed."""

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Literal

import duckdb
import numpy as np

from app.core.errors import AppError
from app.domain.columns.service import ColumnService
from app.domain.compare.analyze import MAX_SERIES, CompareColumn, Comparer
from app.domain.filters.model import Condition, filters_key
from app.domain.filters.scope import scoped_source, where_for
from app.domain.timeseries import autocorrelation as ac
from app.domain.timeseries import breaks as br
from app.domain.timeseries import builder, methods
from app.domain.timeseries import forecast as fc
from app.domain.timeseries import residuals as rs
from app.domain.timeseries import series as ts
from app.domain.timeseries import stationarity as st
from app.domain.timeseries import volatility as vo
from app.domain.timeseries.decomposition import (
    Decomposition,
    DecompositionError,
    decompose,
    trend_component,
)
from app.domain.timeseries.methods import MethodResult
from app.domain.timeseries.seasonality import (
    SeasonalProfile,
    YearOverlay,
    period_end,
    profiles,
    starts,
    year_overlay,
)
from app.domain.variable.source import clean
from app.modules.timeseries.forecasting import ForecastJob, ForecastJobs

DATES = {"datetime"}
NUMBERS = {"numeric_continuous", "numeric_discrete"}
CATEGORIES = {"categorical_nominal", "categorical_ordinal", "boolean"}
SUM_ROLES = ts.SUM_ROLES
CACHE_SIZE = 16


class TimeSeriesError(AppError):
    def __init__(self, message: str, code: str = "time_series") -> None:
        super().__init__(message, code=code, status_code=422)


@dataclass
class Request:
    time: str | None = None
    value: str | None = None
    group: str | None = None
    series: str | None = None  # the group analysed, when grouped
    options: ts.Options = field(default_factory=ts.Options)
    gaps: ts.Gaps = "leave"
    season: int | None = None  # cycle length override, in periods


@dataclass
class SeriesSetup:
    """The configuration actually used: every field chosen or defaulted."""

    time: str
    value: str
    group: str | None
    series: str | None
    dates: list[str]
    numbers: list[str]
    categories: list[str]
    groups: list[str]  # labels of the group column with their own series
    period: ts.Period
    aggregate: ts.Aggregate
    period_auto: bool
    aggregate_auto: bool
    coarsened: bool
    first_partial: bool
    last_partial: bool
    gaps: ts.Gaps
    season: int | None
    periods: int
    rows: int  # rows with a date and a value
    total: int  # rows after the filters


@dataclass
class SeriesLine:
    label: str | None
    values: list[float | None]
    counts: list[int]
    rolling_mean: list[float | None] = field(default_factory=list)
    rolling_std: list[float | None] = field(default_factory=list)


@dataclass
class SeriesFigures:
    start: str
    end: str
    periods: int
    missing: int  # periods without any row
    change: float | None  # last quarter of the series against the first, in %


@dataclass
class SeriesOverview:
    setup: SeriesSetup
    periods: list[str]
    analyzed: SeriesLine
    lines: list[SeriesLine]  # every group, for the overlay (empty when not grouped)
    figures: SeriesFigures
    window: int | None
    align: ts.Align
    methods: list[MethodResult]
    message: str | None = None


@dataclass
class SeriesSeasonality:
    setup: SeriesSetup
    detrend: str  # how the trend was removed before comparing seasons
    profiles: list[SeasonalProfile]
    overlay: YearOverlay | None
    methods: list[MethodResult]
    filled: int  # empty periods interpolated for the methods
    message: str | None = None


@dataclass
class SeriesDecomposition:
    setup: SeriesSetup
    periods: list[str]
    observed: list[float | None]
    result: Decomposition | None
    filled: int
    message: str | None = None


@dataclass
class SeriesStationarity:
    setup: SeriesSetup
    transform: st.Transform
    regression: st.Regression  # deterministic terms of ADF, KPSS and PP: level (c) or trend (ct)
    periods: list[str]  # periods of the transformed series (differences drop the first ones)
    transformed: list[float]
    synthesis: st.Synthesis | None
    suggestion: st.Suggestion | None
    methods: list[MethodResult]
    filled: int
    message: str | None = None


@dataclass
class SeriesAutocorrelation:
    setup: SeriesSetup
    transform: st.Transform
    correlogram: ac.Correlogram | None
    methods: list[MethodResult]
    filled: int
    message: str | None = None


@dataclass
class SeriesVolatility:
    setup: SeriesSetup
    residuals_from: str  # "STL remainder" or "straight-line residuals"
    periods: list[str]
    residuals: list[float]
    rolling_std: list[float | None]
    window: int
    rising: bool | None
    log_helps: bool
    methods: list[MethodResult]
    filled: int
    message: str | None = None


@dataclass
class SeriesResiduals:
    setup: SeriesSetup
    distribution: rs.Distribution | None
    filled: int
    message: str | None = None


@dataclass
class BreakPoint:
    index: int
    period: str
    before: float  # level at the end of the segment that ends (its mean, or its line)
    after: float  # level at the start of the segment that starts
    slope_before: float = 0.0  # per period (trend cost)
    slope_after: float = 0.0


@dataclass
class AnomalyRow:
    index: int
    period: str
    start: str  # ISO bounds of the period, to filter its rows
    end: str
    value: float
    expected: float
    score: float


@dataclass
class SeriesBreaks:
    setup: SeriesSetup
    periods: list[str]
    values: list[float]  # the series searched (without its seasonality when it has one)
    deseasonalized: bool
    breaks: br.Breaks | None
    points: list[BreakPoint]
    methods: list[MethodResult]
    anomalies: list[AnomalyRow]
    anomaly_method: br.Anomaly
    threshold: float
    residuals_from: str
    filled: int
    message: str | None = None


@dataclass
class _Prepared:
    setup: SeriesSetup
    built: builder.Aggregated
    analyzed: SeriesLine
    lines: list[SeriesLine]
    window: int | None  # None: too few periods for rolling statistics
    # The analysed values without incomplete edge periods of a sum or count (their total is too
    # low and would distort every method), with their periods.
    core: list[float | None]
    core_periods: list[str]


def _column(view: Any) -> CompareColumn:
    return CompareColumn(view.name, view.type, view.parser, view.order, view.role)


def _choose(requested: str | None, names: list[str], fallback: str | None) -> str | None:
    return requested if requested in names else fallback


class TimeSeriesService:
    def __init__(self, columns: ColumnService) -> None:
        self.columns = columns
        self._cache: OrderedDict[tuple[Any, ...], _Prepared] = OrderedDict()
        self.forecasts = ForecastJobs()

    def clear(self) -> None:
        self._cache.clear()
        self.forecasts.clear()

    # --- Series --------------------------------------------------------------------------------

    def prepare(self, dataset_id: str, request: Request, conditions: list[Condition]) -> _Prepared:
        dataset = self.columns.ready(dataset_id)
        views = [v for v in self.columns.columns(dataset_id) if not v.excluded]
        by_name = {v.name: v for v in views}
        dates = [v.name for v in views if v.type in DATES]
        numbers = [v.name for v in views if v.type in NUMBERS]
        categories = [v.name for v in views if v.type in CATEGORIES]
        if not dates:
            raise TimeSeriesError("This dataset has no date column.", "needs_date")
        if not numbers:
            raise TimeSeriesError("This dataset has no numeric column.", "needs_number")
        summed = next((n for n in numbers if by_name[n].role in SUM_ROLES), numbers[0])
        time = _choose(request.time, dates, dates[0])
        value = _choose(request.value, numbers, summed)
        group = _choose(request.group, categories, None)
        assert time is not None and value is not None
        options = request.options
        key = (
            dataset_id,
            dataset.imported_at,
            time,
            value,
            group,
            request.series,
            (options.period, options.aggregate, options.window, options.align),
            request.gaps,
            request.season,
            tuple(
                (v.name, v.type, v.role, v.parser.model_dump_json())
                for v in (by_name[time], by_name[value], by_name.get(group or ""))
                if v is not None
            ),
            filters_key(conditions),
        )
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        where = where_for(views, conditions)
        connection = duckdb.connect()
        try:
            source = scoped_source(dataset.storage_path, where, numbered=True)
            comparer = Comparer(
                connection,
                source,
                _column(by_name[time]),
                _column(by_name[value]),
                color=_column(by_name[group]) if group else None,
            )
            aliases = {"t": comparer.x, "v": comparer.y}
            if comparer.color:
                aliases["c"] = comparer.color
            relation = comparer.rows_of(aliases)
            total = comparer.total()
            (rows,) = comparer.one(f"SELECT count(*) FROM {relation}")
            if rows < 3:
                raise TimeSeriesError("Fewer than 3 rows have a date and a value.", "too_few_rows")
            labels = (
                comparer.kept_labels(relation, "c", comparer.color)[:MAX_SERIES]
                if comparer.color
                else None
            )
            built = builder.aggregate(connection, relation, by_name[value].role, options, labels)
        finally:
            connection.close()

        def line(item: builder.Values) -> SeriesLine:
            return SeriesLine(item.label, ts.fill_gaps(item.values, request.gaps), item.counts)

        lines = [line(item) for item in built.groups]
        chosen = None
        if lines:
            chosen = (
                request.series if request.series in [x.label for x in lines] else lines[0].label
            )
        analyzed = next((x for x in lines if x.label == chosen), None) or line(built.overall)
        window = None
        if len(built.periods) >= ts.MIN_PERIODS:
            window = ts.resolve_window(options.window, built.period, len(built.periods))
            for item in {id(x): x for x in [analyzed, *lines]}.values():
                item.rolling_mean, item.rolling_std = ts.rolling(item.values, window, options.align)
        season = request.season or ts.season_length(built.period)
        setup = SeriesSetup(
            time,
            value,
            group,
            chosen,
            dates,
            numbers,
            categories,
            labels or [],
            built.period,
            built.aggregate,
            built.period_auto,
            built.aggregate_auto,
            built.coarsened,
            built.first_partial,
            built.last_partial,
            request.gaps,
            season,
            len(built.periods),
            int(rows),
            total,
        )
        summed = built.aggregate in ("sum", "count")
        start = 1 if built.first_partial and summed else 0
        stop = len(built.periods) - (1 if built.last_partial and summed else 0)
        prepared = _Prepared(
            setup,
            built,
            analyzed,
            lines,
            window,
            analyzed.values[start:stop],
            built.periods[start:stop],
        )
        self._cache[key] = prepared
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)
        return prepared

    # --- Sections ------------------------------------------------------------------------------

    def overview(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        chosen: list[str] | None = None,
    ) -> SeriesOverview:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built, analyzed = prepared.setup, prepared.built, prepared.analyzed
        known = [v for v in analyzed.values if v is not None]
        quarter = max(1, len(known) // 4)
        first = float(np.mean(known[:quarter])) if known else 0.0
        last = float(np.mean(known[-quarter:])) if known else 0.0
        figures = SeriesFigures(
            built.periods[0],
            built.periods[-1],
            len(built.periods),
            sum(1 for count in analyzed.counts if count == 0),
            clean((last - first) / abs(first) * 100) if first else None,
        )
        message = None
        results: list[MethodResult] = []
        if setup.periods < ts.MIN_PERIODS:
            message = f"Too few periods to analyse ({ts.MIN_PERIODS} needed)."
        else:
            tested = builder.trend_input(built, analyzed.values)
            for key in chosen or methods.DEFAULT_TREND:
                results.append(methods.TREND[key](tested, setup.season))
        return SeriesOverview(
            setup,
            built.periods,
            analyzed,
            prepared.lines,
            figures,
            prepared.window,
            request.options.align,
            results,
            message,
        )

    def seasonality(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        chosen: list[str] | None = None,
    ) -> SeriesSeasonality:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built = prepared.setup, prepared.built
        if setup.periods < ts.MIN_PERIODS:
            message = f"Too few periods to analyse ({ts.MIN_PERIODS} needed)."
            return SeriesSeasonality(setup, "", [], None, [], 0, message)
        series, filled = ts.complete(prepared.core)
        trend, detrend = trend_component(series, setup.season)
        detrended = series - trend
        moments = starts(prepared.core_periods, built.period)
        results = []
        for key in chosen or methods.DEFAULT_SEASONALITY:
            method, wants_detrended = methods.SEASONALITY[key]
            results.append(method(detrended if wants_detrended else series, setup.season))
        return SeriesSeasonality(
            setup,
            detrend,
            profiles(built.period, moments, series, detrended),
            year_overlay(built.period, moments, prepared.core),
            results,
            filled,
        )

    def _transformed(
        self, prepared: _Prepared, how: st.Transform
    ) -> tuple[np.ndarray, np.ndarray, int, str | None]:
        """The complete series, its transformation, the interpolated periods, or why not."""
        series, filled = ts.complete(prepared.core)
        if prepared.setup.periods < st.MIN_PERIODS:
            return series, series, filled, f"Needs at least {st.MIN_PERIODS} periods."
        try:
            return series, st.transform(series, how, prepared.setup.season), filled, None
        except st.TransformError as error:
            return series, series, filled, str(error)

    def stationarity(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        how: st.Transform = "none",
        chosen: list[str] | None = None,
    ) -> SeriesStationarity:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built = prepared.setup, prepared.built
        series, changed, filled, problem = self._transformed(prepared, how)
        view = SeriesStationarity(setup, how, "c", [], [], None, None, [], filled, problem)
        if problem:
            return view
        regression: st.Regression = "c"
        if how in ("none", "log") and setup.season and len(changed) >= 2 * setup.season:
            try:
                parts = decompose(changed, "stl", setup.season, built.period)
                if (parts.strength_trend or 0) > 0.6:
                    regression = "ct"  # a strong trend: test stationarity around it
            except DecompositionError:
                pass
        view.regression = regression
        view.periods = prepared.core_periods[len(prepared.core_periods) - len(changed) :]
        view.transformed = [float(v) for v in changed]
        keys = chosen or list(st.DEFAULT_STATIONARITY)
        results = {key: st.STATIONARITY[key](changed, regression) for key in keys}
        adf = results.get("adf") or st.adf(changed, regression)
        kpss = results.get("kpss") or st.kpss_test(changed, regression)
        view.synthesis = st.synthesis(adf, kpss)
        view.suggestion = st.suggest(series, setup.season)
        view.methods = list(results.values())
        return view

    def autocorrelation(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        how: st.Transform = "none",
        chosen: list[str] | None = None,
        pacf: ac.PacfMethod = "ywm",
    ) -> SeriesAutocorrelation:
        prepared = self.prepare(dataset_id, request, conditions)
        setup = prepared.setup
        _, changed, filled, problem = self._transformed(prepared, how)
        view = SeriesAutocorrelation(setup, how, None, [], filled, problem)
        if problem:
            return view
        view.correlogram = ac.correlogram(changed, setup.season, pacf)
        view.methods = [
            ac.AUTOCORRELATION[key](changed, setup.season)
            for key in chosen or ac.DEFAULT_AUTOCORRELATION
        ]
        return view

    def volatility(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        chosen: list[str] | None = None,
    ) -> SeriesVolatility:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built = prepared.setup, prepared.built
        series, filled = ts.complete(prepared.core)
        window = prepared.window or ts.resolve_window(None, built.period, max(setup.periods, 8))
        view = SeriesVolatility(setup, "", [], [], [], window, None, False, [], filled)
        if setup.periods < vo.MIN_PERIODS:
            view.message = f"Needs at least {vo.MIN_PERIODS} periods."
            return view
        found = rs.remainder(series, setup.season)
        spread = vo.rolling_spread(found.values, window)
        direction = vo.summary(series, spread, found.fitted)
        view.residuals_from = found.method
        view.periods = prepared.core_periods
        view.residuals = [float(v) for v in found.values]
        view.rolling_std = spread
        view.rising, view.log_helps = direction.rising, direction.log_helps
        view.methods = [vo.VOLATILITY[key](found.values) for key in chosen or vo.DEFAULT_VOLATILITY]
        return view

    def residuals(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        source: rs.Source = "residuals",
    ) -> SeriesResiduals:
        prepared = self.prepare(dataset_id, request, conditions)
        series, filled = ts.complete(prepared.core)
        view = SeriesResiduals(prepared.setup, None, filled)
        try:
            view.distribution = rs.distribution(series, source, prepared.setup.season)
        except rs.DistributionError as error:
            view.message = str(error)
        return view

    def breaks(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        search: br.Search = "pelt",
        cost: br.Cost | Literal["auto"] = "auto",
        sensitivity: br.Sensitivity = "medium",
        chosen: list[str] | None = None,
        anomaly: br.Anomaly = "robust_z",
        threshold: float = 3.5,
    ) -> SeriesBreaks:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built = prepared.setup, prepared.built
        series, filled = ts.complete(prepared.core)
        view = SeriesBreaks(setup, [], [], False, None, [], [], [], anomaly, threshold, "", filled)
        if setup.periods < 10:
            view.message = "Needs at least 10 periods."
            return view
        values, deseasonalized = rs.deseasonalized(series, setup.season)
        chosen_cost: br.Cost
        if cost == "auto":
            # A steady trend cut into mean levels gives a staircase of false breaks.
            trending = methods.mann_kendall_test([float(v) for v in values]).significant
            chosen_cost = "trend" if trending else "mean"
        else:
            chosen_cost = cost
        found = br.find_breaks(values, search, chosen_cost, sensitivity, setup.season)
        found.cost_auto = cost == "auto"
        view.periods, view.values, view.deseasonalized = (
            prepared.core_periods,
            [float(v) for v in values],
            deseasonalized,
        )
        view.breaks = found
        view.points = [
            BreakPoint(
                point,
                prepared.core_periods[point],
                before.last if chosen_cost == "trend" else before.mean,
                after.first if chosen_cost == "trend" else after.mean,
                before.slope,
                after.slope,
            )
            for point, before, after in zip(
                found.points, found.segments, found.segments[1:], strict=False
            )
        ]
        view.methods = [br.BREAK_TESTS[key](values) for key in chosen or br.DEFAULT_BREAK_TESTS]
        remainder = rs.remainder(series, setup.season)
        view.residuals_from = remainder.method
        moments = starts(prepared.core_periods, built.period)
        view.anomalies = [
            AnomalyRow(
                point.index,
                prepared.core_periods[point.index],
                moments[point.index].isoformat(),
                period_end(moments[point.index], built.period).isoformat(),
                point.value,
                point.expected,
                point.score,
            )
            for point in br.anomalies(remainder.values, series, anomaly, threshold)
        ]
        return view

    def start_forecast(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        horizon: int | None = None,
        chosen: list[str] | None = None,
        order: tuple[int, int, int] = (1, 1, 1),
        seasonal_order: tuple[int, int, int] = (0, 0, 0),
    ) -> ForecastJob:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built = prepared.setup, prepared.built
        if setup.periods < 10:
            raise TimeSeriesError("A forecast needs at least 10 periods.", "too_few_periods")
        horizon = horizon or fc.default_horizon(built.period, len(prepared.core))
        keys = chosen or list(fc.DEFAULT_MODELS)
        if not setup.season:
            keys = [key for key in keys if key not in ("seasonal_naive", "holt_winters")] or [
                "naive"
            ]
        models = {
            key: fc.sarima_manual(order, seasonal_order) if key == "sarima" else fc.MODELS[key]
            for key in keys
        }
        key = (
            id(prepared),
            tuple(prepared.core_periods[-3:]),
            len(prepared.core),
            horizon,
            tuple(keys),
            order,
            seasonal_order,
        )
        return self.forecasts.start(
            key,
            prepared.core,
            prepared.core_periods,
            built.period,
            setup.season,
            horizon,
            models,
        )

    def decomposition(
        self,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        method: str = "stl",
    ) -> SeriesDecomposition:
        prepared = self.prepare(dataset_id, request, conditions)
        setup, built = prepared.setup, prepared.built
        series, filled = ts.complete(prepared.core)
        observed = [None if v is None else float(v) for v in prepared.core]
        view = SeriesDecomposition(setup, prepared.core_periods, observed, None, filled)
        if not setup.season:
            view.message = "Yearly data has no cycle to separate."
            return view
        try:
            view.result = decompose(series, method, setup.season, built.period)  # type: ignore[arg-type]
        except DecompositionError as error:
            view.message = str(error)
        return view
