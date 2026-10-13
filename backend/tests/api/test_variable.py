import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from tests.api.test_profiling import import_path


@pytest.fixture
def traps(client: TestClient) -> str:
    return import_path(client, default_samples_dir() / "typing_traps.csv")


def get(client: TestClient, dataset_id: str, path: str = "", **params):
    return client.get(f"/api/v1/datasets/{dataset_id}/variable{path}", params=params)


def test_numeric_profile(client: TestClient, traps: str) -> None:
    response = get(client, traps, column="price_eur")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["type"] == "numeric_continuous"
    numeric = body["numeric"]
    assert numeric["describe"]["count"] > 500 and numeric["describe"]["skewness"] > 2
    assert len(numeric["normality"]["tests"]) == 5
    assert numeric["qq"]["theoretical"] and numeric["kde"]["y"] and numeric["ecdf"]["x"]
    assert body["categorical"] is None


def test_fit_and_outliers(client: TestClient, traps: str) -> None:
    fit = get(client, traps, "/fit", column="price_eur").json()
    result = get(client, traps, "/outliers", column="price_eur", method="robust").json()

    assert fit["laws"] and fit["laws"][0]["aic"] <= fit["laws"][-1]["aic"]
    assert {t["key"] for t in fit["transforms"]} >= {"log", "boxcox"}
    assert result["method"] == "robust" and len(result["rules"]) == 4
    assert all(row["row"] >= 1 for row in result["rows"])


def test_profiles_by_type(client: TestClient, traps: str) -> None:
    city = get(client, traps, column="city").json()
    signup = get(client, traps, column="signup_date").json()
    comment = get(client, traps, column="comment").json()
    customer = get(client, traps, column="customer_id").json()

    assert city["categorical"]["distinct"] > 3
    assert signup["date"]["min"] and signup["date"]["step"]
    assert comment["text"]["words"]
    assert customer["identifier"]["unique_pct"] == 100


def test_fit_refuses_a_non_numeric_column(client: TestClient, traps: str) -> None:
    response = get(client, traps, "/fit", column="city")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "not_numeric"


def test_unknown_column(client: TestClient, traps: str) -> None:
    assert get(client, traps, column="nope").status_code == 404


@pytest.mark.slow
def test_five_million_rows_stay_fast(client: TestClient, tmp_path: Path) -> None:
    import duckdb

    path = tmp_path / "big.parquet"
    duckdb.execute(
        "COPY (SELECT range AS id, exp(random() * 3) + random() AS amount FROM range(5000000)) "
        f"TO '{path.as_posix()}' (FORMAT parquet)"
    )
    dataset_id = import_path(client, path)

    start = time.perf_counter()
    profile = get(client, dataset_id, column="amount")
    profile_seconds = time.perf_counter() - start
    start = time.perf_counter()
    fit = get(client, dataset_id, "/fit", column="amount")
    fit_seconds = time.perf_counter() - start

    assert profile.status_code == fit.status_code == 200
    assert profile_seconds < 3, profile_seconds
    assert fit_seconds < 5, fit_seconds
