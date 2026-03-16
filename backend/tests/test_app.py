from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app

client = TestClient(create_app(frontend_dist_dir=Path(__file__).resolve().parents[1] / "static"))


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_requires_authentication() -> None:
    response = client.get("/api/hello")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_hello_after_login() -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert login_response.status_code == 200

    hello_response = client.get("/api/hello")

    assert hello_response.status_code == 200
    assert hello_response.json() == {"message": "Hello from FastAPI, user"}


def test_root_serves_html_with_api_call_button() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Hello world from FastAPI" in response.text
    assert 'id="api-button"' in response.text
