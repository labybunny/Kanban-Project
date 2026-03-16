from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app


@pytest.fixture
def frontend_dist_dir(tmp_path: Path) -> Path:
    dist_dir = tmp_path / "frontend"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    return dist_dir


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "pm.db"


@pytest.fixture
def client(frontend_dist_dir: Path, db_path: Path) -> TestClient:
    app = create_app(frontend_dist_dir=frontend_dist_dir, db_path=db_path)
    with TestClient(app) as test_client:
        yield test_client
