from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app

client = TestClient(create_app(frontend_dist_dir=Path(__file__).resolve().parents[1] / "static"))


def test_auth_me_requires_session() -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_login_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_and_logout_session_flow() -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"username": "user"}

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json() == {"username": "user"}

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"status": "logged_out"}

    me_after_logout_response = client.get("/api/auth/me")
    assert me_after_logout_response.status_code == 401
    assert me_after_logout_response.json() == {"detail": "Unauthorized"}
