import pytest
from pydantic import ValidationError

from app.ai_structured import AiStructuredResponse, apply_operations
from app.board_schema import DEFAULT_BOARD_STATE


def test_ai_structured_response_validates_expected_shape() -> None:
    parsed = AiStructuredResponse.model_validate(
        {
            "assistantResponse": "Updated the board.",
            "operations": [
                {
                    "type": "rename_column",
                    "columnId": "col-backlog",
                    "title": "Roadmap",
                }
            ],
        }
    )

    assert parsed.assistantResponse == "Updated the board."
    assert len(parsed.operations) == 1


def test_ai_structured_response_rejects_missing_response() -> None:
    with pytest.raises(ValidationError):
        AiStructuredResponse.model_validate({"operations": []})


def test_ai_structured_response_rejects_unknown_operation_type() -> None:
    with pytest.raises(ValidationError):
        AiStructuredResponse.model_validate(
            {
                "assistantResponse": "Done",
                "operations": [{"type": "unknown_op"}],
            }
        )


def test_apply_operations_handles_add_move_update_delete() -> None:
    ai_response = AiStructuredResponse.model_validate(
        {
            "assistantResponse": "Applied updates.",
            "operations": [
                {
                    "type": "rename_column",
                    "columnId": "col-backlog",
                    "title": "Ideas",
                },
                {
                    "type": "add_card",
                    "columnId": "col-backlog",
                    "title": "AI generated",
                    "details": "Created by AI",
                },
                {
                    "type": "move_card",
                    "cardId": "card-1",
                    "targetColumnId": "col-review",
                },
                {
                    "type": "update_card",
                    "cardId": "card-2",
                    "title": "Signals updated",
                },
                {
                    "type": "delete_card",
                    "cardId": "card-3",
                },
            ],
        }
    )

    next_state = apply_operations(DEFAULT_BOARD_STATE, ai_response.operations)

    renamed_column = next(column for column in next_state.columns if column.id == "col-backlog")
    assert renamed_column.title == "Ideas"
    assert any(card.title == "AI generated" for card in next_state.cards.values())
    assert "card-1" in next(
        column.cardIds for column in next_state.columns if column.id == "col-review"
    )
    assert next_state.cards["card-2"].title == "Signals updated"
    assert "card-3" not in next_state.cards
