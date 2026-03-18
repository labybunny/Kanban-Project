import os
import logging
import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.ai_client import (
    OPENROUTER_MODEL,
    OpenRouterConfigurationError,
    OpenRouterRequestError,
    OpenRouterStructuredOutputError,
    call_openrouter_chat,
    call_openrouter_structured_json,
)
from app.ai_structured import (
    AiStructuredResponse,
    ConversationTurn,
    apply_operations,
)
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
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str


class BoardUpdateRequest(BaseModel):
    state: BoardState


class BoardResponse(BaseModel):
    boardKey: str
    state: BoardState


class AiTestRequest(BaseModel):
    prompt: str = "What is 2+2? Reply with just the number."


class AiTestResponse(BaseModel):
    model: str
    prompt: str
    output: str


class AiChatRequest(BaseModel):
    message: str
    history: list[ConversationTurn] = Field(default_factory=list)
    boardKey: str = DEFAULT_BOARD_KEY


class AiChatResponse(BaseModel):
    model: str
    boardKey: str
    assistantResponse: str
    boardUpdated: bool
    state: BoardState
    warning: str | None = None


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


def build_ai_messages(
    *,
    board_state: BoardState,
    message: str,
    history: list[ConversationTurn],
) -> list[dict[str, str]]:
    board_json = json.dumps(board_state.model_dump(mode="json"), separators=(",", ":"))
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project management assistant for a kanban board. "
                "Return JSON that matches the required schema. "
                "Use operations only when a board change is needed."
            ),
        }
    ]

    for turn in history:
        messages.append({"role": turn.role, "content": turn.content})

    messages.append(
        {
            "role": "user",
            "content": (
                f"Current board JSON: {board_json}\n"
                f"User message: {message.strip()}"
            ),
        }
    )
    return messages


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

    # Temporarily open for Part 8 connectivity verification.
    @app.post("/api/ai/test", response_model=AiTestResponse)
    def ai_test(payload: AiTestRequest) -> AiTestResponse:
        prompt = payload.prompt.strip() or "What is 2+2? Reply with just the number."
        try:
            output = call_openrouter_chat(prompt)
        except OpenRouterConfigurationError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
        except OpenRouterRequestError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            ) from error

        return AiTestResponse(model=OPENROUTER_MODEL, prompt=prompt, output=output)

    @app.post("/api/ai/chat", response_model=AiChatResponse)
    def ai_chat(
        payload: AiChatRequest,
        username: str = Depends(get_current_username),
    ) -> AiChatResponse:
        normalized_board_key = normalize_board_key(payload.boardKey)
        user_message = payload.message.strip()
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message must not be empty",
            )

        with open_connection(resolved_db_path) as connection:
            user_id = ensure_user(connection, username)
            ensure_board(connection, user_id, normalized_board_key, DEFAULT_BOARD_STATE)
            current_board_state = read_board_state(connection, user_id, normalized_board_key)

        logger.info(
            "ai_chat request user=%s board=%s history_items=%s",
            username,
            normalized_board_key,
            len(payload.history),
        )

        try:
            raw_response = call_openrouter_structured_json(
                messages=build_ai_messages(
                    board_state=current_board_state,
                    message=user_message,
                    history=payload.history,
                ),
                schema_name="kanban_assistant_response",
                schema=AiStructuredResponse.model_json_schema(),
            )
            ai_response = AiStructuredResponse.model_validate(raw_response)
        except OpenRouterConfigurationError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
        except OpenRouterStructuredOutputError:
            logger.warning("ai_chat structured output malformed user=%s", username)
            return AiChatResponse(
                model=OPENROUTER_MODEL,
                boardKey=normalized_board_key,
                assistantResponse=(
                    "I could not safely process that AI response. "
                    "No board changes were applied."
                ),
                boardUpdated=False,
                state=current_board_state,
                warning="Malformed AI output was ignored.",
            )
        except OpenRouterRequestError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            ) from error
        except Exception as error:
            logger.warning("ai_chat structured validation failed user=%s error=%s", username, error)
            return AiChatResponse(
                model=OPENROUTER_MODEL,
                boardKey=normalized_board_key,
                assistantResponse=(
                    "I could not safely process that AI response. "
                    "No board changes were applied."
                ),
                boardUpdated=False,
                state=current_board_state,
                warning="Invalid AI output was ignored.",
            )

        try:
            next_board_state = apply_operations(current_board_state, ai_response.operations)
        except ValueError as error:
            logger.warning(
                "ai_chat rejected operations user=%s board=%s error=%s",
                username,
                normalized_board_key,
                error,
            )
            return AiChatResponse(
                model=OPENROUTER_MODEL,
                boardKey=normalized_board_key,
                assistantResponse=ai_response.assistantResponse,
                boardUpdated=False,
                state=current_board_state,
                warning=f"Rejected unsafe operation(s): {error}",
            )

        board_updated = next_board_state.model_dump(mode="json") != current_board_state.model_dump(
            mode="json"
        )
        persisted_state = next_board_state
        if board_updated:
            with open_connection(resolved_db_path) as connection:
                user_id = ensure_user(connection, username)
                persisted_state = upsert_board_state(
                    connection,
                    user_id,
                    normalized_board_key,
                    next_board_state,
                )

        logger.info(
            "ai_chat completed user=%s board=%s operations=%s updated=%s",
            username,
            normalized_board_key,
            len(ai_response.operations),
            board_updated,
        )
        return AiChatResponse(
            model=OPENROUTER_MODEL,
            boardKey=normalized_board_key,
            assistantResponse=ai_response.assistantResponse,
            boardUpdated=board_updated,
            state=persisted_state,
        )

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
