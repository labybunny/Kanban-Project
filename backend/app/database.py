from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.board_schema import BoardState

SCHEMA_VERSION = 1

SCHEMA_SQL = """
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
"""


def open_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def serialize_board_state(state: BoardState) -> str:
    return json.dumps(state.model_dump(mode="json"), separators=(",", ":"))


def parse_board_state(raw_json: str) -> BoardState:
    return BoardState.model_validate(json.loads(raw_json))


def ensure_user(connection: sqlite3.Connection, username: str) -> int:
    row = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row:
        return int(row["id"])

    cursor = connection.execute(
        "INSERT INTO users (username) VALUES (?)",
        (username,),
    )
    connection.commit()
    return int(cursor.lastrowid)


def ensure_board(
    connection: sqlite3.Connection,
    user_id: int,
    board_key: str,
    default_state: BoardState,
) -> None:
    row = connection.execute(
        "SELECT id FROM boards WHERE user_id = ? AND board_key = ?",
        (user_id, board_key),
    ).fetchone()
    if row:
        return

    connection.execute(
        """
        INSERT INTO boards (user_id, board_key, title, state_json, state_schema_version)
        VALUES (?, ?, 'My Board', ?, ?)
        """,
        (user_id, board_key, serialize_board_state(default_state), SCHEMA_VERSION),
    )
    connection.commit()


def read_board_state(
    connection: sqlite3.Connection,
    user_id: int,
    board_key: str,
) -> BoardState:
    row = connection.execute(
        "SELECT state_json FROM boards WHERE user_id = ? AND board_key = ?",
        (user_id, board_key),
    ).fetchone()
    if not row:
        raise ValueError("Board not found")

    return parse_board_state(str(row["state_json"]))


def upsert_board_state(
    connection: sqlite3.Connection,
    user_id: int,
    board_key: str,
    board_state: BoardState,
) -> BoardState:
    connection.execute(
        """
        INSERT INTO boards (user_id, board_key, title, state_json, state_schema_version)
        VALUES (?, ?, 'My Board', ?, ?)
        ON CONFLICT (user_id, board_key)
        DO UPDATE SET
          state_json = excluded.state_json,
          state_schema_version = excluded.state_schema_version,
          updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, board_key, serialize_board_state(board_state), SCHEMA_VERSION),
    )
    connection.commit()
    return read_board_state(connection, user_id, board_key)


def initialize_database(
    db_path: Path,
    default_username: str,
    default_board_key: str,
    default_state: BoardState,
) -> None:
    with open_connection(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        user_id = ensure_user(connection, default_username)
        ensure_board(connection, user_id, default_board_key, default_state)
