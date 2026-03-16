from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/hello")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_hello_after_login(client: TestClient) -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert login_response.status_code == 200

    hello_response = client.get("/api/hello")

    assert hello_response.status_code == 200
    assert hello_response.json() == {"message": "Hello from FastAPI, user"}


def test_root_serves_html_with_api_call_button(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Kanban Studio" in response.text
