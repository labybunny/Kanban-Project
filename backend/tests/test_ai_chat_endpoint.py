from fastapi.testclient import TestClient


def login(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200


def test_ai_chat_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/ai/chat", json={"message": "rename backlog to roadmap"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_ai_chat_applies_operations_and_persists(client: TestClient, monkeypatch) -> None:
    login(client)

    def fake_structured_response(**kwargs):  # noqa: ANN003
        assert kwargs["messages"][-1]["content"].startswith("Current board JSON:")
        return {
            "assistantResponse": "Renamed the backlog column.",
            "operations": [
                {
                    "type": "rename_column",
                    "columnId": "col-backlog",
                    "title": "Roadmap",
                }
            ],
        }

    monkeypatch.setattr("app.main.call_openrouter_structured_json", fake_structured_response)

    response = client.post("/api/ai/chat", json={"message": "Rename Backlog to Roadmap"})
    assert response.status_code == 200
    body = response.json()
    assert body["boardUpdated"] is True
    assert body["assistantResponse"] == "Renamed the backlog column."
    assert body["warning"] is None
    assert body["state"]["columns"][0]["title"] == "Roadmap"

    board_response = client.get("/api/boards/main")
    assert board_response.status_code == 200
    assert board_response.json()["state"]["columns"][0]["title"] == "Roadmap"


def test_ai_chat_rejects_unsafe_operations(client: TestClient, monkeypatch) -> None:
    login(client)

    def fake_structured_response(**_kwargs):  # noqa: ANN003
        return {
            "assistantResponse": "Moved the card.",
            "operations": [
                {
                    "type": "move_card",
                    "cardId": "card-1",
                    "targetColumnId": "col-missing",
                }
            ],
        }

    monkeypatch.setattr("app.main.call_openrouter_structured_json", fake_structured_response)
    before = client.get("/api/boards/main").json()["state"]

    response = client.post("/api/ai/chat", json={"message": "Move card-1 to missing column"})
    assert response.status_code == 200
    body = response.json()
    assert body["boardUpdated"] is False
    assert body["warning"] is not None
    assert "Rejected unsafe operation" in body["warning"]
    assert body["state"] == before


def test_ai_chat_ignores_malformed_structured_output(client: TestClient, monkeypatch) -> None:
    login(client)

    def fake_structured_response(**_kwargs):  # noqa: ANN003
        return {"operations": []}

    monkeypatch.setattr("app.main.call_openrouter_structured_json", fake_structured_response)

    response = client.post("/api/ai/chat", json={"message": "Hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["boardUpdated"] is False
    assert body["warning"] is not None
    assert "Invalid AI output" in body["warning"]
