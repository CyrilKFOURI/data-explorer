import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from tests.api.test_profiling import import_path


@pytest.fixture
def traps(client: TestClient) -> str:
    return import_path(client, default_samples_dir() / "typing_traps.csv")


def get(client: TestClient, dataset_id: str, **params):
    return client.get(f"/api/v1/datasets/{dataset_id}/correlations", params=params)


def test_matrix_and_insights_of_a_dataset(client: TestClient, traps: str) -> None:
    body = get(client, traps).json()

    matrix = body["matrix"]
    names = [c["name"] for c in matrix["columns"]]
    assert {"age", "income", "country"} <= set(names)
    assert "customer_id" in {e["name"] for e in matrix["excluded"]}
    assert len(matrix["values"]) == len(names) and len(matrix["clustered"]) == len(names)
    assert matrix["rows"] == matrix["total"] == 600 and not matrix["sampled"]
    assert body["insights"] and all(i["link"]["x"] for i in body["insights"])
    # city determines country: a redundancy between categories.
    assert any(
        i["kind"] == "redundant" and set(i["columns"]) == {"country", "city"}
        for i in body["insights"]
    )
    assert any(i["kind"] == "skewed" and i["columns"] == ["price_eur"] for i in body["insights"])


def test_method_columns_and_filters(client: TestClient, traps: str) -> None:
    body = get(
        client,
        traps,
        method="spearman",
        columns="age,income,segment",
        filters=json.dumps([{"column": "country", "op": "in", "values": ["FR"]}]),
    ).json()

    matrix = body["matrix"]
    assert matrix["method"] == "spearman"
    assert [c["name"] for c in matrix["columns"]] == ["age", "segment", "income"]  # file order
    assert matrix["total"] < 600


def test_unknown_method_is_rejected(client: TestClient, traps: str) -> None:
    assert get(client, traps, method="kendall").status_code == 422


@pytest.mark.slow
def test_sixty_columns_on_five_million_rows(client: TestClient, tmp_path: Path) -> None:
    import duckdb

    numbers = ", ".join(f"random() * {i + 1} AS n{i}" for i in range(50))
    categories = ", ".join(
        f"['a', 'b', 'c', 'd'][1 + (range * {2 * i + 1} + {i}) % 4] AS c{i}" for i in range(10)
    )
    path = tmp_path / "wide.parquet"
    duckdb.execute(
        f"COPY (SELECT {numbers}, {categories} FROM range(5000000)) "
        f"TO '{path.as_posix()}' (FORMAT parquet)"
    )
    dataset_id = import_path(client, path)

    start = time.perf_counter()
    response = get(client, dataset_id)
    seconds = time.perf_counter() - start

    assert response.status_code == 200, response.text
    assert len(response.json()["matrix"]["columns"]) == 60
    assert seconds < 10, seconds
