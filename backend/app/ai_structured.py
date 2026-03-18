from __future__ import annotations

from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.board_schema import BoardState, validate_board_state


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class RenameColumnOperation(BaseModel):
    type: Literal["rename_column"]
    columnId: str = Field(min_length=1)
    title: str = Field(min_length=1)


class AddCardOperation(BaseModel):
    type: Literal["add_card"]
    columnId: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str = ""


class UpdateCardOperation(BaseModel):
    type: Literal["update_card"]
    cardId: str = Field(min_length=1)
    title: str | None = None
    details: str | None = None


class DeleteCardOperation(BaseModel):
    type: Literal["delete_card"]
    cardId: str = Field(min_length=1)


class MoveCardOperation(BaseModel):
    type: Literal["move_card"]
    cardId: str = Field(min_length=1)
    targetColumnId: str = Field(min_length=1)
    beforeCardId: str | None = None


AiOperation = Annotated[
    RenameColumnOperation
    | AddCardOperation
    | UpdateCardOperation
    | DeleteCardOperation
    | MoveCardOperation,
    Field(discriminator="type"),
]


class AiStructuredResponse(BaseModel):
    assistantResponse: str = Field(min_length=1)
    operations: list[AiOperation] = Field(default_factory=list)


def _find_column_by_id(columns: list[dict], column_id: str) -> dict:
    for column in columns:
        if column["id"] == column_id:
            return column
    raise ValueError(f"Column not found: {column_id}")


def _find_column_containing_card(columns: list[dict], card_id: str) -> dict:
    for column in columns:
        if card_id in column["cardIds"]:
            return column
    raise ValueError(f"Card not found in board columns: {card_id}")


def _generate_card_id(cards: dict[str, dict]) -> str:
    while True:
        candidate = f"card-{uuid4().hex[:10]}"
        if candidate not in cards:
            return candidate


def apply_operations(board_state: BoardState, operations: list[AiOperation]) -> BoardState:
    if not operations:
        return board_state

    state = board_state.model_dump(mode="python")
    columns: list[dict] = state["columns"]
    cards: dict[str, dict] = state["cards"]

    for operation in operations:
        if isinstance(operation, RenameColumnOperation):
            column = _find_column_by_id(columns, operation.columnId)
            column["title"] = operation.title
            continue

        if isinstance(operation, AddCardOperation):
            column = _find_column_by_id(columns, operation.columnId)
            card_id = _generate_card_id(cards)
            cards[card_id] = {
                "id": card_id,
                "title": operation.title,
                "details": operation.details,
            }
            column["cardIds"].append(card_id)
            continue

        if isinstance(operation, UpdateCardOperation):
            if operation.cardId not in cards:
                raise ValueError(f"Card not found: {operation.cardId}")
            if operation.title is None and operation.details is None:
                raise ValueError("update_card requires title or details")

            if operation.title is not None:
                cards[operation.cardId]["title"] = operation.title
            if operation.details is not None:
                cards[operation.cardId]["details"] = operation.details
            continue

        if isinstance(operation, DeleteCardOperation):
            if operation.cardId not in cards:
                raise ValueError(f"Card not found: {operation.cardId}")
            del cards[operation.cardId]
            for column in columns:
                column["cardIds"] = [card_id for card_id in column["cardIds"] if card_id != operation.cardId]
            continue

        if isinstance(operation, MoveCardOperation):
            if operation.cardId not in cards:
                raise ValueError(f"Card not found: {operation.cardId}")

            source_column = _find_column_containing_card(columns, operation.cardId)
            target_column = _find_column_by_id(columns, operation.targetColumnId)

            source_column["cardIds"] = [
                card_id for card_id in source_column["cardIds"] if card_id != operation.cardId
            ]

            if operation.beforeCardId:
                if operation.beforeCardId not in target_column["cardIds"]:
                    raise ValueError(f"beforeCardId not found in target column: {operation.beforeCardId}")
                target_index = target_column["cardIds"].index(operation.beforeCardId)
                target_column["cardIds"].insert(target_index, operation.cardId)
            else:
                target_column["cardIds"].append(operation.cardId)
            continue

    next_state = BoardState.model_validate(state)
    validate_board_state(next_state)
    return next_state
