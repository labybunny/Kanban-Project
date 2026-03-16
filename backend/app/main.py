import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

VALID_USERNAME = "user"
VALID_PASSWORD = "password"


class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_username(request: Request) -> str:
    username = request.session.get("username")
    if username != VALID_USERNAME:
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


def create_app(frontend_dist_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Project Management MVP API")
    dist_dir = frontend_dist_dir or resolve_frontend_dist_dir()
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

    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
    return app


app = create_app()
