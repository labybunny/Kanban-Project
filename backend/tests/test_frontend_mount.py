from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app


def test_frontend_dist_is_served_from_root(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    client = TestClient(create_app(frontend_dist_dir=tmp_path, db_path=tmp_path / "pm.db"))

    response = client.get("/")

    assert response.status_code == 200
    assert "Kanban Studio" in response.text


def test_api_routes_take_precedence_over_frontend_mount(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    client = TestClient(create_app(frontend_dist_dir=tmp_path, db_path=tmp_path / "pm.db"))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
