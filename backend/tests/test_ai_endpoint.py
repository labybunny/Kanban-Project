from fastapi.testclient import TestClient


def test_ai_test_endpoint_returns_output(client: TestClient, monkeypatch) -> None:
    def fake_call(_: str) -> str:
        return "4"

    monkeypatch.setattr("app.main.call_openrouter_chat", fake_call)
    response = client.post("/api/ai/test", json={"prompt": "What is 2+2?"})

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "openai/gpt-oss-120b:free"
    assert body["output"] == "4"


def test_ai_test_endpoint_missing_key_error(client: TestClient, monkeypatch) -> None:
    from app.ai_client import OpenRouterConfigurationError

    def fake_call(_: str) -> str:
        raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")

    monkeypatch.setattr("app.main.call_openrouter_chat", fake_call)
    response = client.post("/api/ai/test", json={"prompt": "What is 2+2?"})

    assert response.status_code == 503
    assert "OPENROUTER_API_KEY" in response.json()["detail"]


def test_ai_test_endpoint_provider_error(client: TestClient, monkeypatch) -> None:
    from app.ai_client import OpenRouterRequestError

    def fake_call(_: str) -> str:
        raise OpenRouterRequestError("OpenRouter error (500)")

    monkeypatch.setattr("app.main.call_openrouter_chat", fake_call)
    response = client.post("/api/ai/test", json={"prompt": "What is 2+2?"})

    assert response.status_code == 502
    assert "OpenRouter error" in response.json()["detail"]
