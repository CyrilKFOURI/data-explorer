from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.registry import MODULES, Module, mount_modules


def test_registered_module_route_responds(client: TestClient) -> None:
    response = client.get("/api/v1/modules/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from the demo module"}


def test_module_ids_are_unique() -> None:
    ids = [module.id for module in MODULES]
    assert len(ids) == len(set(ids))


def test_unregistered_module_is_not_mounted() -> None:
    app = FastAPI()
    mount_modules(app, "/api/v1", modules=[])

    assert TestClient(app).get("/api/v1/modules/hello").status_code == 404


def test_mount_uses_module_id_as_path() -> None:
    hello = next(module for module in MODULES if module.id == "hello")
    app = FastAPI()
    mount_modules(app, "/api/v1", modules=[Module(id="other", router=hello.router)])

    assert TestClient(app).get("/api/v1/modules/other").status_code == 200
