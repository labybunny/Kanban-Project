# Database Model (Part 5)

## Scope

This document proposes the SQLite schema and data modeling approach for Kanban persistence.
This is a design and sign-off document only. CRUD implementation starts in Part 6 after approval.

## Goals

- Persist board state per `user` and `board`
- Keep MVP simple (single board in product behavior), but keep schema extensible for future multi-board support
- Store board state as JSON (as decided)
- Keep backend as source of truth for validating writes

## Design Summary

- Database engine: SQLite
- Main entities:
  - `users`
  - `boards`
- Board payload storage: JSON text column with `json_valid(...)` constraint
- Board identity: composite `user_id + board_key`
  - MVP uses `board_key = "main"` for one board per user
  - Future boards can use additional keys without schema rewrite

## Proposed Schema (v1)

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  board_key TEXT NOT NULL DEFAULT 'main',
  title TEXT NOT NULL DEFAULT 'My Board',
  state_json TEXT NOT NULL,
  state_schema_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE (user_id, board_key),
  CHECK (json_valid(state_json))
);

CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
```

## Why This Schema

- `users` is minimal and supports multiple users.
- `boards` stores one row per board with JSON payload.
- `UNIQUE(user_id, board_key)` enforces one canonical board for MVP (`main`) while allowing future board keys.
- `state_schema_version` allows JSON shape evolution without immediate table refactors.

## Board JSON Shape (v1)

The stored JSON must match the frontend board structure:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Card title",
      "details": "Card details"
    }
  }
}
```

## Validation Rules (backend)

Validation should run before any write to `boards.state_json`.

1. Root object must contain:
   - `columns` (array)
   - `cards` (object map)
2. Column rules:
   - `id` non-empty string, unique across columns
   - `title` string
   - `cardIds` array of strings
3. Card map rules:
   - each key points to card object with `id`, `title`, `details` strings
   - card object `id` matches its map key
4. Cross-reference rules:
   - every `cardId` in columns must exist in `cards`
   - each card ID appears in exactly one column
5. Constraints:
   - reject unknown top-level structures that break expected board format
   - reject malformed JSON or structurally invalid payloads

## Initialization Strategy

On backend startup (or first DB access):

1. Ensure DB directory exists.
2. Open SQLite connection.
3. Apply `PRAGMA foreign_keys = ON`.
4. Run `CREATE TABLE IF NOT EXISTS` statements for v1 schema.
5. Ensure dummy MVP user exists (`username = "user"`).
6. Ensure default board exists for that user:
   - `board_key = "main"`
   - `state_json` initialized from default board seed

This allows fresh local runs without manual DB setup.

## Migration Strategy

Use SQL migration files and a migration tracking table.

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Recommended layout:

- `backend/migrations/0001_initial.sql` (tables + indexes)
- `backend/migrations/0002_...sql` (future changes)

Rules:

- Apply migrations in ascending version order inside a transaction.
- Record each applied version in `schema_migrations`.
- Never edit an already-applied migration; add a new one instead.

## Test Plan for Part 6 Implementation

When Part 6 is implemented, add tests for:

- DB auto-creation on fresh environment
- table/index creation and foreign key behavior
- default user and default board initialization
- read/write board state by `user_id + board_key`
- invalid JSON and invalid board-shape rejection
- authorization safety (no cross-user board access)

## Sign-Off Request

Please confirm this schema/modeling approach for Part 5.
After approval, Part 6 will implement this design in backend code and tests.
