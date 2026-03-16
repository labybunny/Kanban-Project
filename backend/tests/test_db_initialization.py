import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_database_is_created_on_fresh_environment(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>", encoding="utf-8")

    db_path = tmp_path / "fresh.db"
    assert not db_path.exists()

    app = create_app(frontend_dist_dir=frontend_dir, db_path=db_path)
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200

    assert db_path.exists()


def test_schema_and_default_records_are_created(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir(parents=True, exist_ok=True)
    (frontend_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>", encoding="utf-8")

    db_path = tmp_path / "schema.db"
    app = create_app(frontend_dist_dir=frontend_dir, db_path=db_path)
    with TestClient(app):
        pass

    connection = sqlite3.connect(db_path)
    try:
        users_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        boards_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='boards'"
        ).fetchone()

        assert users_table is not None
        assert boards_table is not None

        user_row = connection.execute(
            "SELECT id, username FROM users WHERE username = 'user'"
        ).fetchone()
        assert user_row is not None

        board_row = connection.execute(
            """
            SELECT id FROM boards
            WHERE user_id = ? AND board_key = 'main'
            """,
            (user_row[0],),
        ).fetchone()
        assert board_row is not None
    finally:
        connection.close()
