"""Shared test fixtures with async SQLAlchemy session factory."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

from infra.database import create_engine_and_session
from infra.embedder_openai import OpenAIEmbedder
from infra.llm_openai import OpenAILLM
from infra.repository import PgVectorRepository
from settings import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def session_factory(settings: Settings) -> async_sessionmaker:
    async_dsn = settings.DAO_URL().replace("postgresql://", "postgresql+asyncpg://")
    engine, factory = create_engine_and_session(async_dsn)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def repo(session_factory) -> PgVectorRepository:
    return PgVectorRepository(session_factory)


@pytest_asyncio.fixture(autouse=True)
async def cleanup(request) -> AsyncGenerator[None, None]:
    if request.node.get_closest_marker("no_db"):
        yield
        return

    settings = Settings()  # type: ignore[call-arg]
    async_dsn = settings.DAO_URL().replace("postgresql://", "postgresql+asyncpg://")
    engine, factory = create_engine_and_session(async_dsn)
    repo = PgVectorRepository(factory)
    try:
        await repo.delete_all()
        yield
    finally:
        await repo.delete_all()
        await engine.dispose()


@pytest_asyncio.fixture
async def embedder(settings: Settings) -> OpenAIEmbedder:
    return OpenAIEmbedder(
        model=settings.EMBED_MODEL,
        base_url=settings.EMBED_BASE_URL,
        api_key=settings.EMBED_API_KEY,
    )


@pytest_asyncio.fixture
async def llm(settings: Settings) -> OpenAILLM:
    return OpenAILLM(
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )
