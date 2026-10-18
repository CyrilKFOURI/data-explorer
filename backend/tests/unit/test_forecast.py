import numpy as np
import pytest

from app.domain.timeseries import forecast as fc

RNG = np.random.default_rng(12)
T = np.arange(120)
SEASONAL = 100 + 10 * np.sin(2 * np.pi * T / 12) + 0.3 * T + RNG.normal(0, 1, 120)
AR1 = np.zeros(300)
for t in range(1, 300):
    AR1[t] = 0.7 * AR1[t - 1] + RNG.normal()
AR1 += 50


@pytest.mark.parametrize("key", [k for k in fc.MODELS if k != "sarima"])
def test_every_model_forecasts_with_ordered_intervals(key: str) -> None:
    prediction = fc.MODELS[key](SEASONAL, 12, 12)

    assert len(prediction.mean) == 12
    assert np.all(prediction.low95 <= prediction.low80 + 1e-9)
    assert np.all(prediction.low80 <= prediction.mean + 1e-9)
    assert np.all(prediction.mean <= prediction.high80 + 1e-9)
    assert np.all(prediction.high80 <= prediction.high95 + 1e-9)


def test_naive_intervals_widen_with_the_horizon() -> None:
    prediction = fc.naive(AR1, 5, None)
    widths = prediction.high95 - prediction.low95

    assert np.all(np.diff(widths) > 0)
    assert prediction.mean[0] == AR1[-1]


def test_seasonal_naive_intervals_account_for_growth() -> None:
    growing = 100 * 1.15 ** (T / 12) + 10 * np.sin(2 * np.pi * T / 12) + RNG.normal(0, 1, 120)

    scores = fc.evaluate(growing, fc.seasonal_naive, 12, 12)

    assert scores.coverage95 is not None and scores.coverage95 >= 0.5


def test_seasonal_naive_repeats_the_last_cycle() -> None:
    prediction = fc.seasonal_naive(SEASONAL, 24, 12)

    assert prediction.mean[:12] == pytest.approx(SEASONAL[-12:])
    assert prediction.mean[12:] == pytest.approx(SEASONAL[-12:])


def test_seasonal_models_beat_naive_on_a_seasonal_series() -> None:
    naive = fc.evaluate(SEASONAL, fc.naive, 12, 12)
    seasonal = fc.evaluate(SEASONAL, fc.seasonal_naive, 12, 12)
    ets = fc.evaluate(SEASONAL, fc.ets_auto, 12, 12)

    assert seasonal.mase is not None and naive.mase is not None and ets.mase is not None
    assert seasonal.mase < naive.mase and ets.mase < naive.mase


def test_mase_of_the_reference_is_about_one_on_a_random_walk() -> None:
    walk = np.cumsum(RNG.normal(0, 1, 400)) + 100

    scores = fc.evaluate(walk, fc.naive, 1, None)

    assert scores.mase == pytest.approx(1, abs=0.35)


def test_arima_finds_an_ar1() -> None:
    prediction = fc.arima_auto(AR1, 6, None)

    assert prediction.info is not None and prediction.info.startswith("ARIMA(1,0,")


def test_auto_ets_picks_a_seasonal_form() -> None:
    prediction = fc.ets_auto(SEASONAL, 12, 12)

    assert prediction.info is not None
    assert prediction.info.endswith((",A)", ",M)"))


def test_intervals_cover_about_their_level_on_simulated_data() -> None:
    noise = RNG.normal(10, 2, 600)

    scores = fc.evaluate(noise, fc.mean_model, 20, None)

    assert scores.coverage95 is not None and 0.85 <= scores.coverage95 <= 1


def test_origins_and_short_series() -> None:
    assert fc.origins(120, 12, 12) == [84, 90, 96, 102, 108]
    assert fc.origins(36, 9, 12) == [15, 19, 23, 27]
    assert fc.default_horizon("month", 36) == 9 and fc.default_horizon("day", 1000) == 30
    with pytest.raises(fc.ModelError, match="cycle"):
        fc.seasonal_naive(SEASONAL[:10], 3, 12)


def test_run_model_reports_failures_and_residual_checks() -> None:
    failed = fc.run_model("holt_winters", fc.holt_winters, SEASONAL[:20], 3, 12)
    fitted = fc.run_model("ets_auto", fc.ets_auto, SEASONAL, 12, 12)

    assert failed.error and failed.scores is None
    assert fitted.scores is not None and fitted.residual_check is not None
    assert len(fitted.forecast) == 12


def test_reference_improvement() -> None:
    results = [
        fc.run_model(key, fc.MODELS[key], SEASONAL, 12, 12)
        for key in ("naive", "seasonal_naive", "ets_auto")
    ]

    reference = fc.compare_to_reference(results, 12)

    assert reference == "seasonal_naive"
    assert next(r for r in results if r.key == "seasonal_naive").vs_reference == pytest.approx(0)


def test_manual_sarima() -> None:
    model = fc.sarima_manual((1, 1, 1), (0, 1, 1))

    prediction = model(SEASONAL, 6, 12)

    assert prediction.info == "ARIMA(1,1,1)(0,1,1)[12]"


def test_jobs_cancel_between_models_and_reuse_finished_ones() -> None:
    import threading
    import time

    from app.modules.timeseries.forecasting import ForecastJobs, future_periods

    gate = threading.Event()

    def slow(y, h, season):
        gate.wait(5)
        return fc.naive(y, h, season)

    jobs = ForecastJobs(workers=1)
    values: list[float | None] = [float(v) for v in AR1[:60]]
    periods = [f"{2000 + i // 12}-{i % 12 + 1:02d}" for i in range(60)]
    job = jobs.start(
        ("a",), values, periods, "month", None, 3, {"naive": slow, "mean": fc.mean_model}
    )
    jobs.cancel(job.id)
    gate.set()
    for _ in range(100):
        if job.status != "running":
            break
        time.sleep(0.05)
    assert job.status == "cancelled" and job.done == 1

    finished = jobs.start(("b",), values, periods, "month", None, 3, {"naive": fc.naive})
    for _ in range(100):
        if finished.status != "running":
            break
        time.sleep(0.05)
    assert finished.status == "done"
    assert jobs.start(("b",), values, periods, "month", None, 3, {"naive": fc.naive}) is finished
    assert future_periods("2004-12", "month", 2) == ["2005-01", "2005-02"]
