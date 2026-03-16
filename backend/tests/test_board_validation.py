import pytest

from app.board_schema import BoardState, validate_board_state


def test_validate_board_state_accepts_valid_payload() -> None:
    state = BoardState.model_validate(
        {
            "columns": [{"id": "col-a", "title": "A", "cardIds": ["card-1"]}],
            "cards": {
                "card-1": {
                    "id": "card-1",
                    "title": "Card 1",
                    "details": "Details",
                }
            },
        }
    )

    validate_board_state(state)


def test_validate_board_state_rejects_card_key_mismatch() -> None:
    state = BoardState.model_validate(
        {
            "columns": [{"id": "col-a", "title": "A", "cardIds": ["card-1"]}],
            "cards": {
                "card-1": {
                    "id": "card-different",
                    "title": "Card 1",
                    "details": "Details",
                }
            },
        }
    )

    with pytest.raises(ValueError, match="mismatch"):
        validate_board_state(state)


def test_validate_board_state_rejects_missing_card_reference() -> None:
    state = BoardState.model_validate(
        {
            "columns": [{"id": "col-a", "title": "A", "cardIds": ["card-missing"]}],
            "cards": {},
        }
    )

    with pytest.raises(ValueError, match="missing card"):
        validate_board_state(state)
