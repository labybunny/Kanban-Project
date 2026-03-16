from __future__ import annotations

from pydantic import BaseModel, Field


class Card(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str


class Column(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cardIds: list[str]


class BoardState(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]


def validate_board_state(state: BoardState) -> None:
    column_ids: set[str] = set()
    card_counts: dict[str, int] = {}

    for column in state.columns:
        if column.id in column_ids:
            raise ValueError(f"Duplicate column id: {column.id}")
        column_ids.add(column.id)

        for card_id in column.cardIds:
            if card_id not in state.cards:
                raise ValueError(f"Column references missing card id: {card_id}")
            card_counts[card_id] = card_counts.get(card_id, 0) + 1

    for card_id, card in state.cards.items():
        if card.id != card_id:
            raise ValueError(f"Card key/id mismatch for card id: {card_id}")

    missing_from_columns = [card_id for card_id in state.cards if card_counts.get(card_id, 0) == 0]
    if missing_from_columns:
        raise ValueError(f"Cards missing from columns: {', '.join(missing_from_columns)}")

    duplicated_cards = [card_id for card_id, count in card_counts.items() if count > 1]
    if duplicated_cards:
        raise ValueError(f"Cards assigned to multiple columns: {', '.join(duplicated_cards)}")


DEFAULT_BOARD_STATE = BoardState.model_validate(
    {
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
            {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
            {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
            {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
            {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Align roadmap themes",
                "details": "Draft quarterly themes with impact statements and metrics.",
            },
            "card-2": {
                "id": "card-2",
                "title": "Gather customer signals",
                "details": "Review support tags, sales notes, and churn feedback.",
            },
            "card-3": {
                "id": "card-3",
                "title": "Prototype analytics view",
                "details": "Sketch initial dashboard layout and key drill-downs.",
            },
            "card-4": {
                "id": "card-4",
                "title": "Refine status language",
                "details": "Standardize column labels and tone across the board.",
            },
            "card-5": {
                "id": "card-5",
                "title": "Design card layout",
                "details": "Add hierarchy and spacing for scanning dense lists.",
            },
            "card-6": {
                "id": "card-6",
                "title": "QA micro-interactions",
                "details": "Verify hover, focus, and loading states.",
            },
            "card-7": {
                "id": "card-7",
                "title": "Ship marketing page",
                "details": "Final copy approved and asset pack delivered.",
            },
            "card-8": {
                "id": "card-8",
                "title": "Close onboarding sprint",
                "details": "Document release notes and share internally.",
            },
        },
    }
)

