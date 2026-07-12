"""FastAPI application with auto-migration on startup."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.dependencies import build_service
from api.routes import extract as extract_router
from api.routes import ingest as ingest_router
from api.routes import query as query_router
from infra.database import create_engine_and_session
from settings import Settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: setup, auto-migrate, and teardown."""
    settings = Settings()  # type: ignore[call-arg]

    # Build async DSN for SQLAlchemy
    async_dsn = settings.DAO_URL().replace("postgresql://", "postgresql+asyncpg://")
    engine, session_factory = create_engine_and_session(async_dsn)

    # ── Auto-run migrations on startup ────────────────────────────
    import subprocess
    import sys

    print("[INFO] Running database migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[WARN] Migration output: {result.stdout}")
        print(f"[WARN] Migration errors: {result.stderr}")
    print("[INFO] Migrations up to date.")

    # ── Expose session_factory so routes can build ad-hoc services ─
    _app.state.session_factory = session_factory

    # ── Build default service (OpenAI embedder) ────────────────────
    service = build_service(session_factory, embedder_type="openai")
    _app.state.service = service

    print(f"[INFO] RAGService ready — model={settings.LLM_MODEL}, k={settings.K}")
    print("[INFO] API docs at http://localhost:8000/docs")

    yield

    await engine.dispose()
    print("[INFO] Engine disposed.")


def create_app() -> FastAPI:
    """Build and return the FastAPI application."""
    app = FastAPI(
        title="Trabia LLM — RAG API",
        description="API de perguntas e respostas sobre o Relatório da CPMI do 8 de Janeiro",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.include_router(extract_router.router)
    app.include_router(query_router.router)
    app.include_router(ingest_router.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
