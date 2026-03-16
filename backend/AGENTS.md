# Backend

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope (Part 6)

- `app/main.py`
  - FastAPI app entrypoint
  - `GET /api/health` health endpoint
  - Session auth endpoints:
    - `POST /api/auth/login` (`user` / `password`)
    - `POST /api/auth/logout`
    - `GET /api/auth/me`
  - `GET /api/hello` protected API endpoint (session required)
  - Kanban board API endpoints (session required):
    - `GET /api/boards/{board_key}`
    - `PUT /api/boards/{board_key}`
  - Session cookies managed with Starlette `SessionMiddleware`
  - Database initialization on app startup (auto-create)
  - Mounts a frontend static distribution directory at `/`
  - Uses `FRONTEND_DIST_DIR` env var when provided
  - Falls back to local `frontend/out` if present, then `backend/static`
- `app/board_schema.py`
  - Pydantic board models (`Card`, `Column`, `BoardState`)
  - Default board seed state
  - Cross-reference validation for board integrity
- `app/database.py`
  - SQLite schema creation and connection helpers
  - User/board ensure functions
  - Board read and upsert persistence helpers
- `tests/test_app.py`
  - API smoke tests, auth requirement checks, and fallback-root static serving checks
- `tests/test_auth.py`
  - Login success/failure tests
  - Session lifecycle tests for `me` and `logout`
- `tests/test_board_api.py`
  - Authenticated board read/write behavior
  - Invalid payload rejection
  - User-scoped board access checks
- `tests/test_board_validation.py`
  - Unit validation tests for board-shape constraints
- `tests/test_db_initialization.py`
  - Fresh-environment DB creation and schema/default-record checks
- `tests/test_frontend_mount.py`
  - Integration tests validating frontend mount behavior
  - Verifies `/api/*` routes still work when frontend is mounted at `/`
- `pyproject.toml`
  - Python dependencies and test configuration
  - Designed for `uv` workflows (`uv sync`, `uv run`)

## Notes

- Docker multi-stage build compiles the Next.js frontend and copies exported files into `/app/frontend_dist`.
- Runtime serving of the real Kanban UI at `/` is now handled by FastAPI static mounting.
- Backend auth now controls access to protected API routes; frontend only mirrors auth state.
- SQLite persistence now stores board JSON per authenticated user and board key.