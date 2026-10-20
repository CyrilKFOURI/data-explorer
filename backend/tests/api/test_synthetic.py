import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from tests.api.test_profiling import import_path

BASE = "/api/v1/modules/synthetic"


@pytest.fixture
def traps(client: TestClient) -> str:
    return import_path(client, default_samples_dir() / "typing_traps.csv")


def generate(client: TestClient, dataset: str, **body: object) -> dict:
    job = client.post(f"{BASE}/datasets/{dataset}/runs", json=body)
    assert job.status_code == 202, job.text
    deadline = time.monotonic() + 120
    state = job.json()
    while state["status"] == "running" and time.monotonic() < deadline:
        time.sleep(0.2)
        state = client.get(f"{BASE}/jobs/{state['id']}").json()
    assert state["status"] == "done", state
    return client.get(f"{BASE}/datasets/{dataset}/runs/{state['run_id']}").json()


def test_plan_gives_each_column_its_rule(client: TestClient, traps: str) -> None:
    found = client.get(f"{BASE}/datasets/{traps}/plan").json()
    rules = {c["name"]: (c["treatment"], c["rule"]) for c in found["columns"]}
    assert rules["customer_id"] == ("unique", "R-SYN-05")
    assert rules["comment"][0] == "leave" and rules["email"][0] == "leave"
    assert rules["signup_date"] == ("model", "R-SYN-04")
    assert found["method"] == "cart" and found["default_rows"] == 600 and found["smooth"]


def test_a_generation_is_valid_saved_and_reopened(client: TestClient, traps: str) -> None:
    run = generate(client, traps, rows=500)
    report = run["report"]
    assert run["rows"] == 500 and report["scores"]["diagnostic"] == 1.0
    assert set(report["verdicts"]) == {"diagnostic", "quality", "detection", "privacy"}
    assert report["privacy"]["unique_copies"] == 0
    assert {c["column"] for c in report["header"]["left_out"]} >= {"comment", "email"}
    preview = client.get(f"{BASE}/datasets/{traps}/runs/{run['id']}/preview").json()
    assert preview["total"] == 500 and len(preview["rows"]) == 100
    assert "comment" not in preview["columns"]
    ids = [row[preview["columns"].index("customer_id")] for row in preview["rows"]]
    assert all(i.startswith("C") and len(i) == 6 for i in ids) and len(set(ids)) == len(ids)
    listed = client.get(f"{BASE}/datasets/{traps}/runs").json()
    assert [r["id"] for r in listed] == [run["id"]] and listed[0]["scores"]["quality"] > 0.5


def test_treatments_and_bounds_are_applied(client: TestClient, traps: str) -> None:
    run = generate(
        client,
        traps,
        method="copula",
        treatments={"email": "fake", "customer_id": "leave"},
        bounds={"age": {"minimum": 30, "maximum": 60}},
    )
    preview = client.get(f"{BASE}/datasets/{traps}/runs/{run['id']}/preview").json()
    assert "customer_id" not in preview["columns"] and "email" in preview["columns"]
    ages = [
        float(r[preview["columns"].index("age")])
        for r in preview["rows"]
        if r[preview["columns"].index("age")]
    ]
    assert min(ages) >= 30 and max(ages) <= 60
    bad = client.post(f"{BASE}/datasets/{traps}/runs", json={"treatments": {"comment": "model"}})
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "bad_treatment"


def test_on_demand_evaluations_are_kept_with_the_run(client: TestClient, traps: str) -> None:
    run = generate(client, traps, method="bayes")
    path = f"{BASE}/datasets/{traps}/runs/{run['id']}"
    found = client.post(f"{path}/utility", json={"target": "income"}).json()
    assert found["task"] == "regression" and found["test_rows"] > 50
    cap = client.post(
        f"{path}/disclosure", json={"known": ["age", "country"], "sensitive": "segment"}
    ).json()
    assert len(cap["variants"]) == 3
    reopened = client.get(path).json()
    assert reopened["report"]["utility"]["target"] == "income"
    assert reopened["report"]["disclosure"]["sensitive"] == "segment"
    detail = client.get(f"{path}/columns/age", params={"bins": 10, "target": "income"}).json()
    assert len(detail["histogram"]["edges"]) == 11 and detail["target"]["target"] == "income"
    pair = client.get(f"{path}/pairs", params={"a": "country", "b": "age"}).json()
    assert pair["kind"] == "mixed" and pair["boxes"]
    assert client.get(f"{path}/columns/comment").status_code == 404


def test_runs_compare_download_and_delete(client: TestClient, traps: str) -> None:
    first = generate(client, traps, method="cart")
    second = generate(client, traps, method="independent")
    compared = client.get(
        f"{BASE}/datasets/{traps}/runs/compare", params={"runs": f"{first['id']},{second['id']}"}
    ).json()
    assert [r["method"] for r in compared] == ["cart", "independent"]
    csv = client.get(
        f"{BASE}/datasets/{traps}/runs/{first['id']}/download", params={"format": "csv"}
    )
    assert csv.status_code == 200 and csv.text.startswith("customer_id,")
    assert client.delete(f"{BASE}/datasets/{traps}/runs/{second['id']}").status_code == 204
    assert len(client.get(f"{BASE}/datasets/{traps}/runs").json()) == 1


def test_save_as_dataset_copies_the_column_types(client: TestClient, traps: str) -> None:
    run = generate(client, traps)
    made = client.post(f"{BASE}/datasets/{traps}/runs/{run['id']}/dataset").json()["dataset_id"]
    dataset = client.get(f"/api/v1/datasets/{made}").json()
    assert dataset["name"] == "typing_traps (synthetic)" and dataset["status"] == "ready"
    source = {c["name"]: c["type"] for c in client.get(f"/api/v1/datasets/{traps}/columns").json()}
    created = {c["name"]: c["type"] for c in client.get(f"/api/v1/datasets/{made}/columns").json()}
    assert created and all(created[name] == source[name] for name in created)
    origin = client.get(f"{BASE}/origin/{made}").json()
    assert origin == {"source_id": traps, "source_name": "typing_traps", "run_id": run["id"]}
    assert client.get(f"{BASE}/origin/{traps}").json() is None
    again = client.post(f"{BASE}/datasets/{traps}/runs/{run['id']}/dataset").json()["dataset_id"]
    assert again == made


def test_gpu_status_and_compute_setting(client: TestClient) -> None:
    status = client.get("/api/v1/settings/gpu").json()
    assert status["state"] in ("ready", "no_support", "not_found") and status["message"]
    settings = client.get("/api/v1/settings").json()
    assert settings["compute"] == {"use_gpu": None}
    settings["compute"]["use_gpu"] = False
    assert client.put("/api/v1/settings", json=settings).json()["compute"]["use_gpu"] is False
    assert client.get("/api/v1/settings").json()["compute"]["use_gpu"] is False


@pytest.mark.slow
def test_fifty_thousand_rows_generate_and_evaluate_within_a_minute(
    client: TestClient, settings, tmp_path
) -> None:
    rng = np.random.default_rng(0)
    rows = 62_500  # 80 % = 50 000 training rows
    data = {f"n{i}": rng.normal(size=rows).round(3) for i in range(14)}
    data.update({f"c{i}": rng.choice(list("abcdefgh"), rows) for i in range(5)})
    data["day"] = pd.Timestamp("2020-01-01") + pd.to_timedelta(
        rng.integers(0, 1_500, rows), unit="D"
    )
    path = settings.home / "uploads" / "perf" / "perf.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(data).to_parquet(path)
    dataset = import_path(client, path)
    started = time.perf_counter()
    run = generate(client, dataset, rows=50_000)
    assert run["train_rows"] == 50_000
    assert time.perf_counter() - started < 60


def test_a_deep_model_trains_with_its_progress_and_device(client: TestClient, traps: str) -> None:
    pytest.importorskip("torch")
    found = client.get(f"{BASE}/datasets/{traps}/plan").json()
    methods = {m["key"]: m for m in found["methods"]}
    assert methods["ctgan"]["available"] and methods["tvae"]["epochs"] == 300
    run = generate(client, traps, method="tvae", epochs=10, device="cpu", rows=300)
    fitted = run["report"]["fitted"]
    assert fitted["device"] == "CPU" and fitted["epochs"] == 10
    assert run["report"]["scores"]["diagnostic"] == 1.0
    listed = client.get(f"{BASE}/datasets/{traps}/runs").json()
    assert listed[0]["device"] == "CPU" and listed[0]["method_label"] == "TVAE"
    bad = client.post(f"{BASE}/datasets/{traps}/runs", json={"method": "ctgan", "epochs": 5})
    assert bad.status_code == 422
