"""The app and the Python library compute the same results: one engine, two front doors."""

import math
from pathlib import Path
from typing import Any

import cyfouri_data_explorer as dx
import pytest
from fastapi.testclient import TestClient

from app.config import default_samples_dir
from tests.api.test_profiling import import_path

TRAPS = default_samples_dir() / "typing_traps.csv"


def same(api: Any, library: Any, path: str = "") -> None:
    """Equal field by field; floats to 1e-9 (JSON round trip)."""
    if isinstance(api, dict):
        assert isinstance(library, dict), path
        assert set(api) == set(library), f"{path}: {set(api) ^ set(library)}"
        for key in api:
            same(api[key], library[key], f"{path}.{key}")
    elif isinstance(api, list):
        assert isinstance(library, list) and len(api) == len(library), path
        for i, (a, b) in enumerate(zip(api, library, strict=True)):
            same(a, b, f"{path}[{i}]")
    elif isinstance(api, float) or isinstance(library, float):
        assert api is not None and library is not None, f"{path}: {api} != {library}"
        assert math.isclose(api, library, rel_tol=1e-9, abs_tol=1e-12), (
            f"{path}: {api} != {library}"
        )
    else:
        assert api == library, f"{path}: {api!r} != {library!r}"


@pytest.fixture
def both(client: TestClient, tmp_path: Path) -> tuple[str, dx.Dataset]:
    return import_path(client, TRAPS), dx.open(TRAPS, cache_dir=tmp_path)


def test_types_are_the_same(client: TestClient, both: tuple[str, dx.Dataset]) -> None:
    dataset_id, ds = both
    columns = client.get(f"/api/v1/datasets/{dataset_id}/columns").json()
    app = {c["name"]: (c["type"], c["role"], c["parser"]) for c in columns}
    library = {c.name: (c.type, c.role, c.parser.model_dump()) for c in ds.types}
    assert app == library


def test_analyses_are_the_same(client: TestClient, both: tuple[str, dx.Dataset]) -> None:
    dataset_id, ds = both
    base = f"/api/v1/datasets/{dataset_id}"
    same(
        client.get(f"{base}/variable", params={"column": "price_eur"}).json(),
        dx.to_dict(ds.variable("price_eur")),
        "variable",
    )
    same(
        client.get(f"{base}/variable/fit", params={"column": "age"}).json(),
        dx.to_dict(ds.fit("age")),
        "fit",
    )
    same(
        client.get(f"{base}/compare", params={"x": "income", "y": "segment"}).json(),
        dx.to_dict(ds.compare("income", "segment")),
        "compare",
    )
    same(client.get(f"{base}/correlations").json(), dx.to_dict(ds.correlations()), "correlations")


def test_filtered_analyses_are_the_same(client: TestClient, both: tuple[str, dx.Dataset]) -> None:
    dataset_id, ds = both
    condition = dx.Condition(column="country", op="in", values=["FR"])
    filters = f"[{condition.model_dump_json()}]"
    api = client.get(
        f"/api/v1/datasets/{dataset_id}/variable", params={"column": "age", "filters": filters}
    ).json()
    same(api, dx.to_dict(ds.where(condition).variable("age")), "filtered variable")
