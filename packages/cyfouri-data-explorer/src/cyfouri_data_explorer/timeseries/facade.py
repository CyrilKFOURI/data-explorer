"""One time series of a dataset, for the library: the app's Time series page as methods.

series = ds.timeseries(time="date", value="sales")
series.overview(); series.stationarity(); series.forecast(horizon=12)
"""

import time as clock
from typing import Literal

from cyfouri_data_explorer.errors import ExplorerError
from cyfouri_data_explorer.filters.model import Condition
from cyfouri_data_explorer.timeseries import autocorrelation as ac
from cyfouri_data_explorer.timeseries import breaks as br
from cyfouri_data_explorer.timeseries import residuals as rs
from cyfouri_data_explorer.timeseries import stationarity as st
from cyfouri_data_explorer.timeseries.forecasting import SeriesForecast
from cyfouri_data_explorer.timeseries.service import (
    Request,
    SeriesAutocorrelation,
    SeriesBreaks,
    SeriesDecomposition,
    SeriesOverview,
    SeriesResiduals,
    SeriesSeasonality,
    SeriesSetup,
    SeriesStationarity,
    SeriesVolatility,
    TimeSeriesService,
)


class TimeSeries:
    """A value over time (one series, or one group of a grouped series). Unset choices (time
    column, period, aggregation, season) are made by the app's rules; `setup()` shows them."""

    def __init__(
        self,
        service: TimeSeriesService,
        dataset_id: str,
        request: Request,
        conditions: list[Condition],
        methods: list[str] | None = None,
    ) -> None:
        self._service = service
        self._id = dataset_id
        self.request = request
        self._conditions = conditions
        self._methods = methods  # the tests to run (None: the default ones ★)

    def _args(self) -> tuple[str, Request, list[Condition]]:
        return self._id, self.request, self._conditions

    def setup(self) -> SeriesSetup:
        """Every choice actually used: time column, value, period, aggregation, season."""
        return self.overview().setup

    def overview(self) -> SeriesOverview:
        """The series, its rolling mean and spread, its trend (Mann-Kendall, Sen's slope)."""
        return self._service.overview(*self._args(), self._methods)

    def seasonality(self) -> SeriesSeasonality:
        return self._service.seasonality(*self._args(), self._methods)

    def decomposition(self, method: str = "stl") -> SeriesDecomposition:
        """Trend, seasonal and remainder (`stl`, `mstl`, `classical`…)."""
        return self._service.decomposition(*self._args(), method)

    def stationarity(self, transform: st.Transform = "none") -> SeriesStationarity:
        """ADF, KPSS, Phillips–Perron… and the suggested differencing."""
        return self._service.stationarity(*self._args(), transform, self._methods)

    def autocorrelation(
        self,
        transform: st.Transform = "none",
        pacf: ac.PacfMethod = "ywm",
        ar_order: int | None = None,
    ) -> SeriesAutocorrelation:
        """ACF, PACF, Ljung–Box, Durbin–Watson."""
        return self._service.autocorrelation(
            *self._args(), transform, self._methods, pacf, ar_order
        )

    def volatility(self, spread_window: int | None = None) -> SeriesVolatility:
        """Heteroscedasticity tests (Breusch–Pagan, White, ARCH-LM…) and the rolling spread."""
        return self._service.volatility(*self._args(), self._methods, spread_window)

    def residuals(self, source: rs.Source = "residuals") -> SeriesResiduals:
        return self._service.residuals(*self._args(), source)

    def breaks(
        self,
        search: br.Search = "pelt",
        cost: br.Cost | Literal["auto"] = "auto",
        sensitivity: br.Sensitivity = "medium",
        anomaly: br.Anomaly = "robust_z",
        threshold: float = 3.5,
    ) -> SeriesBreaks:
        """Change points and anomalies."""
        return self._service.breaks(
            *self._args(), search, cost, sensitivity, self._methods, anomaly, threshold
        )

    def forecast(
        self,
        horizon: int | None = None,
        models: list[str] | None = None,
        order: tuple[int, int, int] = (1, 1, 1),
        seasonal_order: tuple[int, int, int] = (0, 0, 0),
    ) -> SeriesForecast:
        """Naive models, ETS, ARIMA… validated on rolling origins and ranked by MASE (waits for
        every model)."""
        job = self._service.start_forecast(*self._args(), horizon, models, order, seasonal_order)
        while job.status == "running":
            clock.sleep(0.05)
        if job.result is None:
            raise ExplorerError(job.error or "The forecast failed.", code="forecast")
        return job.result
