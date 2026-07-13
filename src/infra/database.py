"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def create_engine_and_session(dsn: str) -> tuple:
    """Create an async SQLAlchemy engine and session factory.

    The DSN should use the asyncpg dialect, e.g.:
        postgresql+asyncpg://user:pass@host:port/db
    """
    engine = create_async_engine(dsn, pool_size=5, max_overflow=10, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, session_factory


async def get_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session (for FastAPI dependencies)."""
    async with session_factory() as session:
        yield session
