from pathlib import Path

from fastapi.testclient import TestClient

from app.board_schema import BoardState
from app.database import ensure_user, open_connection, upsert_board_state


def login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def make_board_state(title: str) -> BoardState:
    return BoardState.model_validate(
        {
            "columns": [
                {
                    "id": "col-main",
                    "title": title,
                    "cardIds": ["card-1"],
                }
            ],
            "cards": {
                "card-1": {
                    "id": "card-1",
                    "title": "Single card",
                    "details": "Details",
                }
            },
        }
    )


def test_board_read_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/boards/main")

    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_authenticated_board_read_returns_default_board(client: TestClient) -> None:
    login(client)

    response = client.get("/api/boards/main")

    assert response.status_code == 200
    payload = response.json()
    assert payload["boardKey"] == "main"
    assert "columns" in payload["state"]
    assert "cards" in payload["state"]
    assert len(payload["state"]["columns"]) > 0


def test_authenticated_board_update_persists_changes(client: TestClient) -> None:
    login(client)
    initial_board_response = client.get("/api/boards/main")
    assert initial_board_response.status_code == 200
    board_state = initial_board_response.json()["state"]

    board_state["columns"][0]["title"] = "Renamed Backlog"
    update_response = client.put("/api/boards/main", json={"state": board_state})
    assert update_response.status_code == 200
    assert update_response.json()["state"]["columns"][0]["title"] == "Renamed Backlog"

    second_read_response = client.get("/api/boards/main")
    assert second_read_response.status_code == 200
    assert second_read_response.json()["state"]["columns"][0]["title"] == "Renamed Backlog"


def test_invalid_board_payload_is_rejected(client: TestClient) -> None:
    login(client)
    invalid_state = {
        "columns": [{"id": "col-a", "title": "A", "cardIds": ["card-missing"]}],
        "cards": {},
    }

    response = client.put("/api/boards/main", json={"state": invalid_state})

    assert response.status_code == 422
    assert "missing card" in response.json()["detail"].lower()


def test_board_access_is_scoped_to_authenticated_user(client: TestClient, db_path: Path) -> None:
    with open_connection(db_path) as connection:
        other_user_id = ensure_user(connection, "other-user")
        upsert_board_state(
            connection,
            user_id=other_user_id,
            board_key="main",
            board_state=make_board_state("Other User Board"),
        )

    login(client)
    response = client.get("/api/boards/main")

    assert response.status_code == 200
    assert response.json()["state"]["columns"][0]["title"] != "Other User Board"
