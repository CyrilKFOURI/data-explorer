"""Forecast a series and compare models honestly on a rolling-origin validation.

Every model returns point forecasts with 80 % and 95 % prediction intervals. Models are scored
on the last periods they did not see (several origins), against a naive reference (MASE).
"""

import itertools
import math
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.forecasting.theta import ThetaModel
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.domain.timeseries import stationarity as st
from app.domain.timeseries.autocorrelation import ljung_box
from app.domain.timeseries.decomposition import stl, strength
from app.domain.timeseries.methods import MethodResult
from app.domain.variable.source import clean

Z80, Z95 = float(stats.norm.ppf(0.9)), float(stats.norm.ppf(0.975))
ARIMA_BUDGET = 20.0  # seconds for the automatic ARIMA search
MAX_SEASONAL_ARIMA = 24  # longer cycles make seasonal ARIMA impractical (weekly data, m = 52)
HORIZON = {"hour": 24, "day": 30, "week": 12, "month": 12, "quarter": 8, "year": 3}


def default_horizon(period: str, periods: int) -> int:
    """The usual horizon for the period, at most a quarter of the series (room to validate)."""
    return max(1, min(HORIZON[period], periods // 4))


@dataclass
class Prediction:
    mean: np.ndarray
    low80: np.ndarray
    high80: np.ndarray
    low95: np.ndarray
    high95: np.ndarray
    info: str | None = None  # chosen form or orders, e.g. "ETS(A,Ad,A)", "ARIMA(1,1,1)"
    resid: np.ndarray | None = None  # in-sample residuals (for diagnostics)


class ModelError(ValueError):
    """The model cannot be fitted on this series (too short, values ≤ 0…)."""


def _quiet(compute: Callable):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return compute()


def _band(mean: np.ndarray, sigma: np.ndarray, info: str | None = None, resid=None) -> Prediction:
    return Prediction(
        mean,
        mean - Z80 * sigma,
        mean + Z80 * sigma,
        mean - Z95 * sigma,
        mean + Z95 * sigma,
        info,
        resid,
    )


# --- Benchmarks (intervals from Hyndman & Athanasopoulos, FPP3 §5.5) ----------------------------


def _rms(resid: np.ndarray) -> float:
    """Root mean square of the residuals: unlike the standard deviation, it keeps a systematic
    error (a seasonal naive forecast of a growing series is always too low)."""
    return float(np.sqrt(np.mean(resid**2))) if len(resid) else 0.0


def naive(y: np.ndarray, h: int, season: int | None) -> Prediction:
    resid = np.diff(y)
    sigma = _rms(resid)
    steps = np.arange(1, h + 1)
    return _band(np.full(h, y[-1]), sigma * np.sqrt(steps), resid=resid)


def seasonal_naive(y: np.ndarray, h: int, season: int | None) -> Prediction:
    if not season or len(y) < season + 2:
        raise ModelError("Needs a seasonal period and more than one full cycle.")
    resid = y[season:] - y[:-season]
    sigma = _rms(resid)
    steps = np.arange(h)
    mean = np.array([y[len(y) - season + (i % season)] for i in steps])
    cycles = steps // season + 1
    return _band(mean, sigma * np.sqrt(cycles), resid=resid)


def drift(y: np.ndarray, h: int, season: int | None) -> Prediction:
    n = len(y)
    slope = (y[-1] - y[0]) / (n - 1)
    resid = np.diff(y) - slope
    sigma = float(np.std(resid, ddof=1))
    steps = np.arange(1, h + 1)
    return _band(y[-1] + slope * steps, sigma * np.sqrt(steps * (1 + steps / (n - 1))), resid=resid)


def mean_model(y: np.ndarray, h: int, season: int | None) -> Prediction:
    sigma = float(np.std(y, ddof=1))
    return _band(
        np.full(h, y.mean()), np.full(h, sigma * math.sqrt(1 + 1 / len(y))), resid=y - y.mean()
    )


# --- Exponential smoothing (ETS state-space models) ----------------------------------------------


def _ets(
    y: np.ndarray,
    h: int,
    error: str,
    trend: str | None,
    damped: bool,
    seasonal: str | None,
    season: int | None,
):
    model = ETSModel(
        pd.Series(y),
        error=error,
        trend=trend,
        damped_trend=damped,
        seasonal=seasonal,
        seasonal_periods=season if seasonal else None,
    )
    return _quiet(lambda: model.fit(disp=False, maxiter=200))


def _ets_prediction(fit, n: int, h: int, label: str) -> Prediction:
    frames = [
        _quiet(lambda a=alpha: fit.get_prediction(start=n, end=n + h - 1).summary_frame(alpha=a))
        for alpha in (0.2, 0.05)
    ]
    mean = np.asarray(frames[0]["mean"], dtype=float)
    return Prediction(
        mean,
        np.asarray(frames[0]["pi_lower"], dtype=float),
        np.asarray(frames[0]["pi_upper"], dtype=float),
        np.asarray(frames[1]["pi_lower"], dtype=float),
        np.asarray(frames[1]["pi_upper"], dtype=float),
        label,
        np.asarray(fit.resid, dtype=float),
    )


def _ets_label(error: str, trend: str | None, damped: bool, seasonal: str | None) -> str:
    code = {"add": "A", "mul": "M", None: "N"}
    return f"ETS({code[error]},{code[trend]}{'d' if damped else ''},{code[seasonal]})"


def ses(y: np.ndarray, h: int, season: int | None) -> Prediction:
    return _ets_prediction(_ets(y, h, "add", None, False, None, season), len(y), h, "ETS(A,N,N)")


def holt(y: np.ndarray, h: int, season: int | None) -> Prediction:
    return _ets_prediction(_ets(y, h, "add", "add", False, None, season), len(y), h, "ETS(A,A,N)")


def holt_winters(y: np.ndarray, h: int, season: int | None) -> Prediction:
    if not season or len(y) < 2 * season + 2:
        raise ModelError("Needs two full cycles.")
    return _ets_prediction(_ets(y, h, "add", "add", False, "add", season), len(y), h, "ETS(A,A,A)")


def ets_auto(y: np.ndarray, h: int, season: int | None) -> Prediction:
    """Every admissible ETS form, the lowest AICc kept (multiplicative only for values > 0)."""
    positive = bool((y > 0).all())
    errors = ["add", "mul"] if positive else ["add"]
    trends: list[tuple[str | None, bool]] = [(None, False), ("add", False), ("add", True)]
    seasonals: list[str | None] = [None]
    if season and 2 <= season <= 52 and len(y) >= 2 * season + 2:
        seasonals += ["add", "mul"] if positive else ["add"]
    best = None
    for error, (trend, damped), seasonal in itertools.product(errors, trends, seasonals):
        if error == "add" and seasonal == "mul":
            continue  # numerically unstable combination (FPP3 §8.6)
        try:
            fit = _ets(y, h, error, trend, damped, seasonal, season)
        except Exception:
            continue
        if np.isfinite(fit.aicc) and (best is None or fit.aicc < best[0].aicc):
            best = (fit, _ets_label(error, trend, damped, seasonal))
    if best is None:
        raise ModelError("No ETS form could be fitted.")
    return _ets_prediction(best[0], len(y), h, best[1])


def theta(y: np.ndarray, h: int, season: int | None) -> Prediction:
    seasonal = bool(season and season >= 2 and len(y) >= 2 * season and (y > 0).all())
    fit = _quiet(
        lambda: ThetaModel(y, period=season if seasonal else 1, deseasonalize=seasonal).fit()
    )
    mean = np.asarray(fit.forecast(h), dtype=float)
    i80 = np.asarray(_quiet(lambda: fit.prediction_intervals(h, alpha=0.2)), dtype=float)
    i95 = np.asarray(_quiet(lambda: fit.prediction_intervals(h, alpha=0.05)), dtype=float)
    return Prediction(
        mean,
        i80[:, 0],
        i80[:, 1],
        i95[:, 0],
        i95[:, 1],
        "Theta" + (" (deseasonalized)" if seasonal else ""),
    )


# --- ARIMA ---------------------------------------------------------------------------------------


def _sarimax(y: np.ndarray, order: tuple[int, int, int], seasonal: tuple[int, int, int, int]):
    model = SARIMAX(
        y, order=order, seasonal_order=seasonal, trend="c" if order[1] + seasonal[1] == 0 else None
    )
    return _quiet(lambda: model.fit(disp=False, maxiter=100))


def _arima_prediction(fit, h: int, label: str) -> Prediction:
    forecast = fit.get_forecast(h)
    mean = np.asarray(forecast.predicted_mean, dtype=float)
    i80 = np.asarray(forecast.conf_int(alpha=0.2), dtype=float)
    i95 = np.asarray(forecast.conf_int(alpha=0.05), dtype=float)
    burn = max(fit.model.k_diff + fit.model.k_seasonal_diff * fit.model.seasonal_periods, 1)
    return Prediction(
        mean,
        i80[:, 0],
        i80[:, 1],
        i95[:, 0],
        i95[:, 1],
        label,
        np.asarray(fit.resid, dtype=float)[burn:],
    )


def _arima_label(order: tuple[int, int, int], seasonal: tuple[int, int, int, int]) -> str:
    text = f"ARIMA({order[0]},{order[1]},{order[2]})"
    if seasonal[3]:
        text += f"({seasonal[0]},{seasonal[1]},{seasonal[2]})[{seasonal[3]}]"
    return text


def differences(y: np.ndarray, season: int | None) -> tuple[int, int, int]:
    """Seasonal differences D (strong seasonality) then d (ADF and KPSS), and the usable cycle."""
    m = season if season and 2 <= season <= MAX_SEASONAL_ARIMA and len(y) >= 3 * season else 0
    seasonal_d = 0
    if m:
        parts = stl(y, m)
        if (strength(parts.seasonal, parts.resid) or 0) > 0.64:
            seasonal_d = 1
    base = y[m:] - y[:-m] if seasonal_d else y
    d = 0
    while d < 2:
        verdict = st.judge(base)
        if verdict is None or verdict.verdict == "stationary":
            break
        base, d = np.diff(base), d + 1
    return d, seasonal_d, m


def arima_auto(y: np.ndarray, h: int, season: int | None) -> Prediction:
    """Hyndman-Khandakar stepwise search, simplified: differences from tests, then neighbours of
    the best (p, q, P, Q) by AICc, within a time budget."""
    d, seasonal_d, m = differences(y, season)
    started = time.monotonic()
    tried: dict[tuple[int, int, int, int], float] = {}
    fits: dict[tuple[int, int, int, int], object] = {}

    def score(p: int, q: int, sp: int, sq: int) -> float:
        key = (p, q, sp, sq)
        if key in tried:
            return tried[key]
        try:
            fit = _sarimax(y, (p, d, q), (sp, seasonal_d, sq, m) if m else (0, 0, 0, 0))
            value = float(fit.aicc) if np.isfinite(fit.aicc) else math.inf
            fits[key] = fit
        except Exception:
            value = math.inf
        tried[key] = value
        return value

    starts = (
        [(2, 2, 1, 1), (0, 0, 0, 0), (1, 0, 1, 0), (0, 1, 0, 1)]
        if m
        else [(2, 2, 0, 0), (0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0)]
    )
    for start in starts:
        score(*start)
    improved = True
    while improved and time.monotonic() - started < ARIMA_BUDGET:
        improved = False
        best = min(tried, key=tried.__getitem__)
        p, q, sp, sq = best
        for dp, dq, dsp, dsq in itertools.product((-1, 0, 1), repeat=4):
            candidate = (p + dp, q + dq, sp + dsp, sq + dsq)
            if (
                min(candidate) < 0
                or candidate[0] > 3
                or candidate[1] > 3
                or candidate[2] > (1 if m else 0)
                or candidate[3] > (1 if m else 0)
                or candidate in tried
            ):
                continue
            if score(*candidate) < tried[best]:
                improved = True
            if time.monotonic() - started > ARIMA_BUDGET:
                break
    best = min(tried, key=tried.__getitem__)
    if not math.isfinite(tried[best]):
        raise ModelError("No ARIMA order could be fitted.")
    p, q, sp, sq = best
    label = _arima_label((p, d, q), (sp, seasonal_d, sq, m))
    if season and season > MAX_SEASONAL_ARIMA:
        label += " (cycle too long for seasonal terms)"
    if time.monotonic() - started > ARIMA_BUDGET:
        label += " (search stopped at the time limit)"
    return _arima_prediction(fits[best], h, label)


def sarima_manual(
    order: tuple[int, int, int], seasonal: tuple[int, int, int]
) -> Callable[[np.ndarray, int, int | None], Prediction]:
    def fit(y: np.ndarray, h: int, season: int | None) -> Prediction:
        m = season if season and seasonal != (0, 0, 0) else 0
        full = (*seasonal, m) if m else (0, 0, 0, 0)
        try:
            result = _sarimax(y, order, full)
        except Exception as error:
            raise ModelError(f"SARIMA could not be fitted: {error}") from error
        return _arima_prediction(result, h, _arima_label(order, full))

    return fit


# --- Regression on time, and machine learning on lags --------------------------------------------


def _season_dummies(t: np.ndarray, season: int | None) -> np.ndarray:
    if not season or season < 2 or season > 52:
        return np.empty((len(t), 0))
    position = t % season
    return np.column_stack([(position == k).astype(float) for k in range(1, season)])


def linear_trend_season(y: np.ndarray, h: int, season: int | None) -> Prediction:
    """Linear regression on a time trend and one indicator per position of the cycle
    (Hyndman's TSLM), with its exact prediction intervals."""
    import statsmodels.api as sm

    n = len(y)
    use_season = bool(season and 2 <= season <= 52 and n >= 2 * season)
    t = np.arange(n + h, dtype=float)
    design = np.column_stack(
        [np.ones(n + h), t, _season_dummies(t, season if use_season else None)]
    )
    fit = _quiet(lambda: sm.OLS(y, design[:n]).fit())
    frames = [fit.get_prediction(design[n:]).summary_frame(alpha=a) for a in (0.2, 0.05)]
    label = "Trend + seasonal dummies" if use_season else "Linear trend"
    return Prediction(
        np.asarray(frames[0]["mean"], dtype=float),
        np.asarray(frames[0]["obs_ci_lower"], dtype=float),
        np.asarray(frames[0]["obs_ci_upper"], dtype=float),
        np.asarray(frames[1]["obs_ci_lower"], dtype=float),
        np.asarray(frames[1]["obs_ci_upper"], dtype=float),
        label,
        np.asarray(fit.resid, dtype=float),
    )


def _lag_model(kind: str) -> Callable[[np.ndarray, int, int | None], Prediction]:
    """Gradient boosting or a small neural network predicting each period from the previous
    ones, on the series with its linear trend removed (trees cannot extrapolate a trend), then
    forecasting one step at a time. Intervals come from the in-sample one-step errors widened
    with the horizon: an approximation, said in the label."""

    def fit(y: np.ndarray, h: int, season: int | None) -> Prediction:
        from sklearn.ensemble import HistGradientBoostingRegressor
        from sklearn.neural_network import MLPRegressor
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        n = len(y)
        lags = max(3, min(season or 12, 24, n // 4))
        if n < lags + 10:
            raise ModelError(f"Needs at least {lags + 10} periods.")
        t = np.arange(n, dtype=float)
        slope, intercept = np.polyfit(t, y, 1)
        rest = y - (slope * t + intercept)

        def features(history: np.ndarray, position: int) -> list[float]:
            row = list(history[-lags:][::-1])
            if season and season >= 2:
                angle = 2 * np.pi * (position % season) / season
                row += [float(np.sin(angle)), float(np.cos(angle))]
            return row

        x = np.array([features(rest[:i], i) for i in range(lags, n)])
        target = rest[lags:]
        if kind == "gbm":
            model = HistGradientBoostingRegressor(
                max_iter=200, learning_rate=0.05, max_leaf_nodes=15, random_state=42
            )
        else:
            model = make_pipeline(
                StandardScaler(),
                MLPRegressor(
                    hidden_layer_sizes=(32, 16), alpha=1e-3, max_iter=2_000, random_state=42
                ),
            )
        _quiet(lambda: model.fit(x, target))
        resid = target - np.asarray(model.predict(x), dtype=float)
        history = list(rest)
        steps = []
        for step in range(h):
            value = float(model.predict(np.array([features(np.array(history), n + step)]))[0])
            history.append(value)
            steps.append(value + slope * (n + step) + intercept)
        sigma = float(np.sqrt(np.mean(resid**2))) * np.sqrt(np.arange(1, h + 1))
        label = (
            "Gradient boosting" if kind == "gbm" else "Neural network (MLP)"
        ) + f" on {lags} lags"
        return _band(np.array(steps), sigma, label + " · approximate intervals", resid)

    return fit


Model = Callable[[np.ndarray, int, int | None], Prediction]
MODELS: dict[str, Model] = {
    "naive": naive,
    "seasonal_naive": seasonal_naive,
    "ets_auto": ets_auto,
    "arima_auto": arima_auto,
    "drift": drift,
    "mean": mean_model,
    "ses": ses,
    "holt": holt,
    "holt_winters": holt_winters,
    "theta": theta,
    "sarima": naive,  # replaced by sarima_manual(...) with the user's orders
    "tslm": linear_trend_season,
    "gbm_lags": _lag_model("gbm"),
    "mlp_lags": _lag_model("mlp"),
}
DEFAULT_MODELS = ("naive", "seasonal_naive", "ets_auto", "arima_auto")


# --- Validation and scores -----------------------------------------------------------------------


@dataclass
class Scores:
    mae: float | None
    rmse: float | None
    mape: float | None  # only when every actual value is above 0
    smape: float | None
    mase: float | None  # < 1: better than the naive reference
    rmsse: float | None
    bias: float | None  # mean error (forecast - actual)
    coverage80: float | None  # share of actual values inside the 80 % interval
    coverage95: float | None
    winkler95: float | None  # interval width plus penalties for misses (lower is better)


@dataclass
class ModelResult:
    key: str
    info: str | None
    scores: Scores | None
    vs_reference: float | None  # relative MASE improvement over the reference, in %
    forecast: list[float] = field(default_factory=list)
    low80: list[float] = field(default_factory=list)
    high80: list[float] = field(default_factory=list)
    low95: list[float] = field(default_factory=list)
    high95: list[float] = field(default_factory=list)
    residual_check: MethodResult | None = None  # Ljung-Box on the residuals (ARIMA, ETS)
    seconds: float = 0.0
    error: str | None = None


def origins(n: int, h: int, season: int | None) -> list[int]:
    """Training lengths of the rolling origins: up to 5, each followed by h unseen periods."""
    minimum = max((season or 1) + 2, 10)  # one cycle; models needing more skip that origin
    found = [n - h - i * max(1, h // 2) for i in range(5)]
    return sorted(t for t in found if t >= minimum)[-5:] or ([n - h] if n - h >= 4 else [])


def _scale(train: np.ndarray, season: int | None) -> tuple[float, float]:
    """In-sample MAE and RMSE of the seasonal naive (naive without a season): MASE, RMSSE scales."""
    m = season if season and len(train) > season + 1 else 1
    diff = train[m:] - train[:-m]
    return float(np.mean(np.abs(diff))) or 1.0, float(np.sqrt(np.mean(diff**2))) or 1.0


def evaluate(y: np.ndarray, model: Model, h: int, season: int | None) -> Scores:
    errors, actuals, scaled_abs, scaled_sq = [], [], [], []
    in80, in95, winkler = [], [], []
    for size in origins(len(y), h, season):
        train, test = y[:size], y[size : size + h]
        if not len(test):
            continue
        try:
            prediction = model(train, len(test), season)
        except ModelError:
            continue  # too little history at this origin for this model
        error = prediction.mean[: len(test)] - test
        mae_scale, rmse_scale = _scale(train, season)
        errors.extend(error)
        actuals.extend(test)
        scaled_abs.extend(np.abs(error) / mae_scale)
        scaled_sq.extend((error / rmse_scale) ** 2)
        in80.extend(
            (test >= prediction.low80[: len(test)]) & (test <= prediction.high80[: len(test)])
        )
        lo, hi = prediction.low95[: len(test)], prediction.high95[: len(test)]
        in95.extend((test >= lo) & (test <= hi))
        width = hi - lo
        penalty = np.where(
            test < lo, 2 / 0.05 * (lo - test), np.where(test > hi, 2 / 0.05 * (test - hi), 0)
        )
        winkler.extend(width + penalty)
    if not errors:
        raise ModelError("The series is too short to validate this horizon.")
    e, a = np.array(errors), np.array(actuals)
    positive = bool((a > 0).all())
    denominator = np.abs(a) + np.abs(a + e)
    return Scores(
        clean(np.mean(np.abs(e))),
        clean(np.sqrt(np.mean(e**2))),
        clean(np.mean(np.abs(e / a)) * 100) if positive else None,
        clean(np.mean(np.where(denominator > 0, 2 * np.abs(e) / denominator, 0)) * 100),
        clean(np.mean(scaled_abs)),
        clean(np.sqrt(np.mean(scaled_sq))),
        clean(np.mean(e)),
        clean(np.mean(in80)),
        clean(np.mean(in95)),
        clean(np.mean(winkler)),
    )


def run_model(key: str, model: Model, y: np.ndarray, h: int, season: int | None) -> ModelResult:
    started = time.monotonic()
    try:
        scores = evaluate(y, model, h, season)
        final = model(y, h, season)
    except (ModelError, ValueError, np.linalg.LinAlgError) as error:
        return ModelResult(
            key, None, None, None, error=str(error), seconds=time.monotonic() - started
        )
    check = None
    if (
        final.resid is not None
        and len(final.resid) >= 20
        and key not in ("naive", "seasonal_naive", "drift", "mean")
    ):
        check = ljung_box(final.resid, season)
    return ModelResult(
        key,
        final.info,
        scores,
        None,
        [float(v) for v in final.mean],
        [float(v) for v in final.low80],
        [float(v) for v in final.high80],
        [float(v) for v in final.low95],
        [float(v) for v in final.high95],
        check,
        time.monotonic() - started,
    )


def compare_to_reference(results: list[ModelResult], season: int | None) -> str:
    """Fill each model's improvement over the naive reference; returns the reference key."""
    reference_key = (
        "seasonal_naive"
        if season and any(r.key == "seasonal_naive" and r.scores for r in results)
        else "naive"
    )
    reference = next((r for r in results if r.key == reference_key and r.scores), None)
    if reference and reference.scores and reference.scores.mase:
        for result in results:
            if result.scores and result.scores.mase is not None:
                result.vs_reference = clean((1 - result.scores.mase / reference.scores.mase) * 100)
    return reference_key
