from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_static(tmp_path: Path) -> Path:
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (static / "assets" / "main.js").write_text("console.log(1)", encoding="utf-8")
    return static


def test_spa_routes_fall_back_to_index(tmp_path: Path) -> None:
    settings = Settings(home=tmp_path / "ws", static_dir=make_static(tmp_path))
    with TestClient(create_app(settings)) as client:
        assert client.get("/settings").text == "<html>app</html>"
        assert client.get("/assets/main.js").text == "console.log(1)"
        assert client.get("/api/v1/unknown").status_code == 404
        assert client.get("/api/v1/health").status_code == 200
