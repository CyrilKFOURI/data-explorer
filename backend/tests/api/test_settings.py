from pathlib import Path

from fastapi.testclient import TestClient

from tests.api.test_profiling import import_path

API = "/api/v1"


def test_settings_defaults_update_and_bounds(client: TestClient) -> None:
    defaults = client.get(f"{API}/settings").json()

    assert defaults["detection"] == {
        "parse_rate": 0.95,
        "empty_rate": 0.95,
        "discrete_max": 20,
        "identifier_unique": 0.95,
    }
    changed = {**defaults["detection"], "discrete_max": 5}
    assert client.put(f"{API}/settings", json={"detection": changed}).status_code == 200
    assert client.get(f"{API}/settings").json()["detection"]["discrete_max"] == 5
    too_low = {**defaults["detection"], "parse_rate": 0.2}
    assert client.put(f"{API}/settings", json={"detection": too_low}).status_code == 422


def test_thresholds_apply_to_the_next_detection(client: TestClient, tmp_path: Path) -> None:
    path = tmp_path / "ratings.csv"
    path.write_text("rating\n" + "\n".join(str(i % 8) for i in range(200)) + "\n", encoding="utf-8")
    dataset_id = import_path(client, path)
    columns = f"{API}/datasets/{dataset_id}/columns"

    assert client.get(columns).json()[0]["type"] == "numeric_discrete"  # 8 values <= 20

    detection = client.get(f"{API}/settings").json()["detection"]
    client.put(f"{API}/settings", json={"detection": {**detection, "discrete_max": 5}})
    redetected = client.post(f"{columns}/detect").json()

    assert redetected[0]["type"] == "numeric_continuous"  # 8 values > 5


def test_storage_and_cache_clearing(client: TestClient, tmp_path: Path) -> None:
    path = tmp_path / "small.csv"
    path.write_text("a,b\n1,x\n2,y\n", encoding="utf-8")
    dataset_id = import_path(client, path)

    storage = client.get(f"{API}/storage").json()
    cleared = client.post(f"{API}/storage/clear-caches")

    assert storage["workspace"] and storage["total_bytes"] > 0
    assert [d["id"] for d in storage["datasets"]] == [dataset_id]
    assert storage["datasets"][0]["bytes"] > 0
    assert cleared.status_code == 204
