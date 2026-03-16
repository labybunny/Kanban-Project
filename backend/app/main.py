import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.board_schema import BoardState, DEFAULT_BOARD_STATE, validate_board_state
from app.database import (
    ensure_board,
    ensure_user,
    initialize_database,
    open_connection,
    read_board_state,
    upsert_board_state,
)

VALID_USERNAME = "user"
VALID_PASSWORD = "password"
DEFAULT_BOARD_KEY = "main"


class LoginRequest(BaseModel):
    username: str
    password: str


class BoardUpdateRequest(BaseModel):
    state: BoardState


class BoardResponse(BaseModel):
    boardKey: str
    state: BoardState


def get_current_username(request: Request) -> str:
    username = request.session.get("username")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    return username


def resolve_frontend_dist_dir() -> Path:
    configured_dir = os.getenv("FRONTEND_DIST_DIR")
    if configured_dir:
        return Path(configured_dir)

    repo_dist = Path(__file__).resolve().parents[2] / "frontend" / "out"
    if repo_dist.exists():
        return repo_dist

    return Path(__file__).resolve().parent.parent / "static"


def resolve_db_path() -> Path:
    configured_path = os.getenv("DB_PATH")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parent.parent / "data" / "pm.db"


def normalize_board_key(board_key: str) -> str:
    normalized = board_key.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid board key",
        )
    return normalized


def create_app(frontend_dist_dir: Path | None = None, db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")
    dist_dir = frontend_dist_dir or resolve_frontend_dist_dir()
    resolved_db_path = db_path or resolve_db_path()
    initialize_database(
        db_path=resolved_db_path,
        default_username=VALID_USERNAME,
        default_board_key=DEFAULT_BOARD_KEY,
        default_state=DEFAULT_BOARD_STATE,
    )
    app.state.db_path = resolved_db_path

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "dev-session-secret-change-me"),
        same_site="lax",
        https_only=False,
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/auth/login")
    def login(payload: LoginRequest, request: Request) -> dict[str, str]:
        if payload.username != VALID_USERNAME or payload.password != VALID_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        request.session["username"] = VALID_USERNAME
        return {"username": VALID_USERNAME}

    @app.post("/api/auth/logout")
    def logout(request: Request) -> dict[str, str]:
        request.session.clear()
        return {"status": "logged_out"}

    @app.get("/api/auth/me")
    def me(username: str = Depends(get_current_username)) -> dict[str, str]:
        return {"username": username}

    @app.get("/api/hello")
    def hello(username: str = Depends(get_current_username)) -> dict[str, str]:
        return {"message": f"Hello from FastAPI, {username}"}

    @app.get("/api/boards/{board_key}", response_model=BoardResponse)
    def read_board(board_key: str, username: str = Depends(get_current_username)) -> BoardResponse:
        normalized_board_key = normalize_board_key(board_key)
        with open_connection(resolved_db_path) as connection:
            user_id = ensure_user(connection, username)
            ensure_board(connection, user_id, normalized_board_key, DEFAULT_BOARD_STATE)
            board_state = read_board_state(connection, user_id, normalized_board_key)

        return BoardResponse(boardKey=normalized_board_key, state=board_state)

    @app.put("/api/boards/{board_key}", response_model=BoardResponse)
    def update_board(
        board_key: str,
        payload: BoardUpdateRequest,
        username: str = Depends(get_current_username),
    ) -> BoardResponse:
        normalized_board_key = normalize_board_key(board_key)
        try:
            validate_board_state(payload.state)
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error

        with open_connection(resolved_db_path) as connection:
            user_id = ensure_user(connection, username)
            board_state = upsert_board_state(connection, user_id, normalized_board_key, payload.state)

        return BoardResponse(boardKey=normalized_board_key, state=board_state)

    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return app


app = create_app()
