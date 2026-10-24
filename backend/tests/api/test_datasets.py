import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.core import db
from app.core.jobs import InlineJobRunner
from app.main import create_app
from app.services.datasets import repository as repo
from tests.factories import SEMICOLON_CSV, write_csv


def import_file(client: TestClient, path: Path, **body: object) -> dict:
    response = client.post("/api/v1/datasets", json={"path": str(path), **body})
    assert response.status_code == 201, response.text
    return response.json()


def test_preview_endpoint(client: TestClient, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", SEMICOLON_CSV)

    response = client.post("/api/v1/sources/preview", json={"path": str(path)})

    assert response.status_code == 200
    body = response.json()
    assert body["csv"]["delimiter"] == ";"
    assert len(body["rows"]) == 3


def test_preview_error_is_readable(client: TestClient, tmp_path: Path) -> None:
    response = client.post("/api/v1/sources/preview", json={"path": str(tmp_path / "nope.csv")})

    assert response.status_code == 422
    assert response.json()["error"]["message"].startswith("Path not found")


def test_import_creates_ready_dataset(client: TestClient, tmp_path: Path) -> None:
    body = import_file(client, write_csv(tmp_path / "sales.csv", SEMICOLON_CSV))

    dataset = body["dataset"]
    assert body["reused"] is False
    assert body["job"]["status"] == "done"
    assert dataset["status"] == "ready"
    assert (dataset["name"], dataset["row_count"], dataset["col_count"]) == ("sales", 3, 3)
    assert dataset["source_state"] == "ok"


def test_import_failure_marks_dataset_in_error(client: TestClient, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", SEMICOLON_CSV)

    body = import_file(client, path, options={"columns": []})

    assert body["dataset"]["status"] == "error"
    assert body["dataset"]["error"] == "Select at least one column to import."
    assert body["job"]["status"] == "failed"


def test_same_source_and_options_reuse_existing_dataset(client: TestClient, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", SEMICOLON_CSV)
    first = import_file(client, path)

    second = import_file(client, path)
    third = import_file(client, path, options={"sample_pct": 50})

    assert second["reused"] is True
    assert second["dataset"]["id"] == first["dataset"]["id"]
    assert third["dataset"]["id"] != first["dataset"]["id"]


def test_list_rename_open_delete(client: TestClient, tmp_path: Path, settings: Settings) -> None:
    dataset_id = import_file(client, write_csv(tmp_path / "a.csv", SEMICOLON_CSV))["dataset"]["id"]

    assert [d["id"] for d in client.get("/api/v1/datasets").json()] == [dataset_id]
    renamed = client.patch(f"/api/v1/datasets/{dataset_id}", json={"name": "  Coffee  "})
    assert renamed.json()["name"] == "Coffee"
    assert client.post(f"/api/v1/datasets/{dataset_id}/open").status_code == 200

    assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 204
    assert client.get("/api/v1/datasets").json() == []
    assert not (settings.home / "datasets" / dataset_id).exists()
    assert (tmp_path / "a.csv").exists()  # the source is never touched


def test_schema_and_head(client: TestClient, tmp_path: Path) -> None:
    dataset_id = import_file(client, write_csv(tmp_path / "a.csv", SEMICOLON_CSV))["dataset"]["id"]

    schema = client.get(f"/api/v1/datasets/{dataset_id}/schema").json()
    head = client.get(f"/api/v1/datasets/{dataset_id}/head?limit=2").json()

    assert [column["name"] for column in schema] == ["nom", "prix", "date"]
    assert head["columns"] == ["nom", "prix", "date"]
    assert head["rows"] == [["Café", "1.5", "2024-01-02"], ["Thé", "2.25", "2024-02-03"]]


def test_source_changes_are_detected(client: TestClient, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "a.csv", SEMICOLON_CSV)
    dataset_id = import_file(client, path)["dataset"]["id"]

    write_csv(path, SEMICOLON_CSV + "Eau;0,5;2024-04-05\n")
    stat = path.stat()
    os.utime(path, (stat.st_atime, stat.st_mtime + 10))
    assert client.get(f"/api/v1/datasets/{dataset_id}").json()["source_state"] == "changed"

    job = client.post(f"/api/v1/datasets/{dataset_id}/reimport").json()
    dataset = client.get(f"/api/v1/datasets/{dataset_id}").json()
    assert job["status"] == "done"
    assert (dataset["row_count"], dataset["source_state"]) == (4, "ok")

    path.unlink()
    assert client.get(f"/api/v1/datasets/{dataset_id}").json()["source_state"] == "missing"
    assert client.post(f"/api/v1/datasets/{dataset_id}/reimport").status_code == 422


def test_unknown_dataset_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/datasets/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_upload_then_import_then_delete_removes_upload(
    client: TestClient, settings: Settings
) -> None:
    upload = client.put(
        "/api/v1/uploads", params={"filename": "../sneaky/data.csv"}, content=SEMICOLON_CSV
    )
    assert upload.status_code == 201
    uploaded = Path(upload.json()["path"])
    assert uploaded.name == "data.csv"
    assert uploaded.is_relative_to(settings.home / "uploads")

    dataset_id = import_file(client, uploaded)["dataset"]["id"]
    client.delete(f"/api/v1/datasets/{dataset_id}")

    assert not uploaded.exists()


def test_upload_rejects_unsupported_and_empty_files(client: TestClient) -> None:
    unsupported = client.put("/api/v1/uploads", params={"filename": "a.exe"}, content=b"x")
    empty = client.put("/api/v1/uploads", params={"filename": "a.csv"}, content=b"")

    assert unsupported.status_code == 415
    assert empty.status_code == 422


def test_samples_are_listed_and_importable(client: TestClient) -> None:
    samples = client.get("/api/v1/samples").json()

    names = {sample["name"] for sample in samples}
    assert {"typing_traps", "sales_timeseries"} <= names
    traps = next(sample for sample in samples if sample["name"] == "typing_traps")
    assert import_file(client, Path(traps["path"]))["dataset"]["row_count"] == 600


def test_restricted_data_dir(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    inside = write_csv(data_dir / "ok.csv", "x\n1\n")
    outside = write_csv(tmp_path / "secret.csv", "x\n1\n")
    settings = Settings(home=tmp_path / "ws", data_dir=data_dir)

    with TestClient(create_app(settings, job_runner=InlineJobRunner())) as client:
        listing = client.get("/api/v1/browse").json()
        escaped = client.get("/api/v1/browse", params={"path": str(data_dir / "..")})
        blocked = client.post("/api/v1/sources/preview", json={"path": str(outside)})
        allowed = client.post("/api/v1/sources/preview", json={"path": str(inside)})

    assert listing["path"] == str(data_dir.resolve())
    assert listing["parent"] is None
    assert [entry["name"] for entry in listing["entries"]] == ["ok.csv"]
    assert escaped.status_code == 422
    assert blocked.status_code == 422
    assert allowed.status_code == 200


def test_restart_marks_interrupted_imports_as_failed(tmp_path: Path, settings: Settings) -> None:
    with TestClient(create_app(settings, job_runner=InlineJobRunner())):
        pass
    connection = db.connect(settings.home / "app.db")
    repo.insert_dataset(
        connection,
        repo.DatasetRecord(
            id="d1", name="x", source_path="x", source_kind="file", format="csv", options="{}",
            fingerprint="f", storage_path="x", status="importing", created_at=repo.now(),
        ),
    )  # fmt: skip
    connection.close()

    with TestClient(create_app(settings, job_runner=InlineJobRunner())) as client:
        dataset = client.get("/api/v1/datasets/d1").json()

    assert dataset["status"] == "error"
    assert dataset["error"].startswith("Interrupted")
