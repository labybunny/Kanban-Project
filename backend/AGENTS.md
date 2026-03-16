# Backend

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope (Part 4)

- `app/main.py`
  - FastAPI app entrypoint
  - `GET /api/health` health endpoint
  - Session auth endpoints:
    - `POST /api/auth/login` (`user` / `password`)
    - `POST /api/auth/logout`
    - `GET /api/auth/me`
  - `GET /api/hello` protected API endpoint (session required)
  - Session cookies managed with Starlette `SessionMiddleware`
  - Mounts a frontend static distribution directory at `/`
  - Uses `FRONTEND_DIST_DIR` env var when provided
  - Falls back to local `frontend/out` if present, then `backend/static`
- `tests/test_app.py`
  - API smoke tests, auth requirement checks, and fallback-root static serving checks
- `tests/test_auth.py`
  - Login success/failure tests
  - Session lifecycle tests for `me` and `logout`
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