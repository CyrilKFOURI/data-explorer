import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from tests.api.test_columns import patch
from tests.api.test_profiling import import_path, write_csv


@pytest.fixture
def traps(client: TestClient) -> str:
    return import_path(client, default_samples_dir() / "typing_traps.csv")


def report(client: TestClient, dataset_id: str, **params) -> tuple[dict, str]:
    started = client.post(f"/api/v1/datasets/{dataset_id}/report", params=params)
    assert started.status_code == 202, started.text
    job = client.get(f"/api/v1/reports/jobs/{started.json()['id']}").json()
    assert job["status"] == "done", job
    file = client.get(f"/api/v1/reports/jobs/{job['id']}/file")
    assert file.status_code == 200
    return job, file.text


def test_report_of_a_dataset(client: TestClient, traps: str) -> None:
    job, page = report(client, traps)

    assert job["file_name"] == "typing_traps-report.html"
    assert page.startswith("<!doctype html>")
    # R-REP-01: self-contained, no script, no link out.
    assert "<script" not in page and "http://" not in page and "https://" not in page
    for section in (
        "findings",
        "glance",
        "variables",
        "relationships",
        "correlations",
        "missing",
        "methods",
    ):
        assert f'id="{section}"' in page
    # one card per analysed column, the ignored ones listed
    columns = client.get(f"/api/v1/datasets/{traps}/columns").json()
    used = [c["name"] for c in columns if c["type"] != "ignored" and not c["excluded"]]
    assert page.count('<article class="variable"') == len(used)
    assert "Left out of the analysis" in page
    # numbers: histogram with density, box plot, QQ-plot, percentiles (R-REP-05, R-REP-06)
    age = page[page.index(">age</h3>") :].split("</article>")[0]
    assert 'class="curve"' in age and "Box plot" in age and "QQ-plot" in age
    assert "Percentiles" in age and "What stands out" in age
    # categories: a Top N in bars
    country = page[page.index(">country</h3>") :].split("</article>")[0]
    assert 'class="bar"' in country
    # correlations: heatmap, strongest links, insights; key findings and drawn pairs
    assert 'aria-label="Association matrix"' in page and "Strongest links" in page
    assert "Insights" in page
    assert page.count('<article class="finding') >= 5
    assert page.count('<article class="pair"') >= 2


def test_report_follows_the_filters(client: TestClient, traps: str) -> None:
    filters = json.dumps([{"column": "country", "op": "in", "values": ["FR"]}])
    overview = client.get(f"/api/v1/datasets/{traps}/overview", params={"filters": filters}).json()

    _, page = report(client, traps, filters=filters)

    assert "Filtered: country is FR" in page
    assert f"{overview['rows']:,} of 600" in page


def test_report_escapes_the_data(client: TestClient, tmp_path: Path) -> None:
    path = write_csv(tmp_path / "x.csv", "<b>x</b>,y\n1,a\n2,b\n3,a\n4,<i>c</i>\n")
    dataset_id = import_path(client, path)

    _, page = report(client, dataset_id)

    assert "<b>x</b>" not in page and "&lt;b&gt;x&lt;/b&gt;" in page
    assert "<i>c</i>" not in page


def test_excluded_columns_are_listed_without_a_card(client: TestClient, traps: str) -> None:
    patch(client, traps, {"name": "age", "excluded": True})

    _, page = report(client, traps)

    assert ">age</h3>" not in page
    assert re.search(r"Left out of the analysis: [^<]*age", page)


def test_unknown_job_and_unready_file(client: TestClient) -> None:
    assert client.get("/api/v1/reports/jobs/nope").status_code == 404
    assert client.get("/api/v1/reports/jobs/nope/file").status_code == 404
    assert client.post("/api/v1/datasets/nope/report").status_code == 404


def test_a_cancelled_report_gives_no_file(client: TestClient, traps: str) -> None:
    service = client.app.state.reports  # type: ignore[attr-defined]
    queued: list = []
    service.runner = type("Later", (), {"submit": lambda self, task: queued.append(task)})()

    job = client.post(f"/api/v1/datasets/{traps}/report").json()
    assert client.delete(f"/api/v1/reports/jobs/{job['id']}").json()["status"] == "running"
    queued[0]()  # the job starts, sees the stop and ends

    assert client.get(f"/api/v1/reports/jobs/{job['id']}").json()["status"] == "cancelled"
    assert client.get(f"/api/v1/reports/jobs/{job['id']}/file").status_code == 409
