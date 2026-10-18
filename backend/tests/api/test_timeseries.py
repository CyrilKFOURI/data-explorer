import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from tests.api.test_profiling import import_path

BASE = "/api/v1/modules/timeseries/datasets"


@pytest.fixture
def sales(client: TestClient) -> str:
    return import_path(client, default_samples_dir() / "sales_timeseries.csv")


def get(client: TestClient, dataset_id: str, section: str, **params):
    return client.get(f"{BASE}/{dataset_id}/{section}", params=params)


def test_overview_opens_already_configured(client: TestClient, sales: str) -> None:
    result = get(client, sales, "overview").json()
    setup = result["setup"]

    assert (setup["time"], setup["value"]) == ("date", "units")  # first quantity / amount
    assert setup["aggregate"] == "sum" and setup["period"] == "week" and setup["coarsened"]
    assert setup["season"] == 52 and setup["rows"] == setup["total"] == 3285
    assert len(result["periods"]) == setup["periods"] == len(result["analyzed"]["values"])
    assert result["window"] == 4 and len(result["analyzed"]["rolling_mean"]) == setup["periods"]
    assert [m["key"] for m in result["methods"]] == ["mann_kendall", "sen"]
    assert result["figures"]["start"] <= result["figures"]["end"]


def test_overview_choices_methods_and_groups(client: TestClient, sales: str) -> None:
    result = get(
        client,
        sales,
        "overview",
        value="revenue",
        period="month",
        agg="mean",
        group="store",
        series="Lyon",
        methods="hamed_rao,cox_stuart,linear_trend",
    ).json()

    assert result["setup"]["period"] == "month" and result["setup"]["aggregate"] == "mean"
    assert result["setup"]["series"] == "Lyon" and result["analyzed"]["label"] == "Lyon"
    assert "Lyon" in result["setup"]["groups"] and len(result["lines"]) >= 2
    assert [m["key"] for m in result["methods"]] == ["hamed_rao", "cox_stuart", "linear_trend"]


def test_seasonality_and_decomposition(client: TestClient, sales: str) -> None:
    season = get(client, sales, "seasonality", period="day", value="revenue").json()

    keys = [p["key"] for p in season["profiles"]]
    assert keys == ["weekday", "month"]
    assert season["overlay"]["unit"] == "week" and len(season["overlay"]["years"]) >= 2
    assert [m["key"] for m in season["methods"]] == ["kruskal_season", "periodogram"]

    parts = get(client, sales, "decomposition", value="revenue").json()
    assert parts["result"]["method"] == "stl" and parts["result"]["seasons"] == [52]
    assert len(parts["result"]["trend"]) == len(parts["periods"])
    assert parts["result"]["strength_seasonal"] is not None

    classical = get(client, sales, "decomposition", value="revenue", method="classical_additive")
    assert classical.json()["result"]["method"] == "classical_additive"


def test_gaps_and_season_override(client: TestClient, sales: str) -> None:
    result = get(client, sales, "decomposition", period="month", season=6).json()

    assert result["setup"]["season"] == 6 and result["result"]["seasons"] == [6]
    assert get(client, sales, "overview", gaps="interpolate").json()["setup"]["gaps"] == (
        "interpolate"
    )


def test_filters_apply(client: TestClient, sales: str) -> None:
    only = json.dumps([{"column": "store", "op": "in", "values": ["Paris"]}])

    result = get(client, sales, "overview", filters=only).json()

    assert result["setup"]["total"] < 3285


def test_errors_are_422(client: TestClient, sales: str) -> None:
    unknown = get(client, sales, "overview", methods="astrology")
    assert unknown.status_code == 422 and unknown.json()["error"]["code"] == "unknown_method"
    assert get(client, sales, "overview", gaps="guess").status_code == 422
    assert get(client, sales, "decomposition", method="x13").status_code == 422


def test_stationarity_and_autocorrelation(client: TestClient, sales: str) -> None:
    raw = get(client, sales, "stationarity", value="revenue").json()

    assert [m["key"] for m in raw["methods"]] == ["adf", "kpss", "phillips_perron"]
    assert raw["synthesis"]["verdict"] in (
        "stationary",
        "unit_root",
        "trend_or_difference",
        "inconclusive",
    )
    assert raw["suggestion"] is None or raw["suggestion"]["verdict"] == "stationary"
    assert len(raw["transformed"]) == len(raw["periods"]) == raw["setup"]["periods"] - 2

    diff = get(
        client, sales, "stationarity", value="revenue", transform="diff", methods="df_gls,rur"
    )
    body = diff.json()
    assert len(body["transformed"]) == body["setup"]["periods"] - 3  # 2 partial weeks, 1 difference
    assert [m["key"] for m in body["methods"]] == ["df_gls", "rur"]
    assert body["synthesis"] is not None  # ADF and KPSS run for the synthesis anyway

    memory = get(client, sales, "autocorrelation", value="revenue", pacf="burg").json()
    assert len(memory["correlogram"]["acf"]) == len(memory["correlogram"]["lags"])
    assert [m["key"] for m in memory["methods"]] == ["ljung_box", "durbin_watson"]
    assert get(client, sales, "autocorrelation", transform="cube").status_code == 422


def test_volatility_residuals_and_breaks(client: TestClient, sales: str) -> None:
    spread = get(
        client, sales, "volatility", value="revenue", methods="breusch_pagan,levene"
    ).json()
    assert spread["residuals_from"] == "STL remainder"
    # incomplete first and last weeks are left out of the analyses
    assert len(spread["residuals"]) == len(spread["rolling_std"]) == len(spread["periods"])
    assert len(spread["periods"]) == spread["setup"]["periods"] - 2
    assert [m["key"] for m in spread["methods"]] == ["breusch_pagan", "levene"]

    for source in ("residuals", "series", "returns"):
        shape = get(client, sales, "residuals", value="revenue", source=source).json()
        assert shape["distribution"]["source"] == source
        assert shape["distribution"]["fit"]["laws"] and shape["distribution"]["normality"]["tests"]

    found = get(
        client, sales, "breaks", value="revenue", sensitivity="high", anomaly="hampel"
    ).json()
    assert found["deseasonalized"] is True and found["breaks"]["search"] == "pelt"
    assert [m["key"] for m in found["methods"]] == ["pettitt"]
    for row in found["anomalies"]:
        assert row["start"] <= row["end"] and row["period"] in found["periods"]
    assert get(client, sales, "breaks", threshold=9).status_code == 422


def test_forecast_job(client: TestClient, sales: str) -> None:
    started = client.post(
        f"{BASE}/{sales}/forecast", params={"value": "revenue", "period": "month", "horizon": 6}
    )
    assert started.status_code == 202, started.text
    job = started.json()
    for _ in range(600):
        job = client.get(f"/api/v1/modules/timeseries/forecast-jobs/{job['id']}").json()
        if job["status"] != "running":
            break
        time.sleep(0.1)
    assert job["status"] == "done", job
    result = job["result"]
    assert result["horizon"] == 6 and len(result["future"]) == 6
    assert result["future"][0] > result["periods"][-1]
    keys = [r["key"] for r in result["results"]]
    assert set(keys) == {"naive", "seasonal_naive", "ets_auto", "arima_auto"}
    assert result["best"] == keys[0] and result["reference"] == "seasonal_naive"
    best = result["results"][0]
    assert len(best["forecast"]) == 6 and best["scores"]["mase"] is not None

    again = client.post(
        f"{BASE}/{sales}/forecast", params={"value": "revenue", "period": "month", "horizon": 6}
    ).json()
    assert again["id"] == job["id"]  # the finished forecast is reused

    manual = client.post(
        f"{BASE}/{sales}/forecast",
        params={"value": "revenue", "period": "month", "methods": "sarima", "order": "1,1,9"},
    )
    assert manual.status_code == 422
    assert client.get("/api/v1/modules/timeseries/forecast-jobs/nope").status_code == 422


def test_ar_order_and_volatility_window(client: TestClient, sales: str) -> None:
    auto = get(client, sales, "autocorrelation", value="revenue").json()["ar"]
    assert auto["chosen_by"] == "AIC" and len(auto["orders"]) >= 5
    assert auto["order"] == min(auto["orders"], key=lambda o: o["aic"])["order"]

    fixed = get(client, sales, "autocorrelation", value="revenue", ar=3).json()["ar"]
    assert fixed["order"] == 3 and fixed["chosen_by"] == "you"
    assert [c["term"] for c in fixed["coefficients"]] == ["const", "lag 1", "lag 2", "lag 3"]

    spread = get(client, sales, "volatility", value="revenue", spread=10).json()
    assert spread["window"] == 10
    assert get(client, sales, "volatility", spread=1).status_code == 422


@pytest.mark.slow
def test_five_million_rows(client: TestClient, tmp_path: Path) -> None:
    import duckdb

    path = tmp_path / "big.parquet"
    duckdb.execute(
        "COPY (SELECT range AS id, random() * 100 AS amount, "
        "DATE '2015-01-01' + CAST(range % 3650 AS INTEGER) AS day FROM range(5000000)) "
        f"TO '{path.as_posix()}' (FORMAT parquet)"
    )
    dataset_id = import_path(client, path)

    start = time.perf_counter()
    response = get(client, dataset_id, "overview", time="day", value="amount")
    seconds = time.perf_counter() - start
    assert response.status_code == 200, response.text
    assert seconds < 2, seconds
