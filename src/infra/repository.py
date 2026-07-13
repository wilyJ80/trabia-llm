"""PostgreSQL + pgvector repository using SQLAlchemy ORM — implements RepositoryPort.

Uses the SQLAlchemy ORM query API together with pgvector's
built-in distance functions instead of raw SQL, avoiding
parameter-binding fragility.

Accepts a ``model_class`` parameter so the same repository can
work with different vector-dimension tables (chunk / chunk_spacy).
"""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.models import Chunk, ChunkResult
from core.port.repository_port import RepositoryPort
from infra.models import ChunkModel


class PgVectorRepository(RepositoryPort):
    """Repository that stores and queries chunks using SQLAlchemy ORM + pgvector.

    Parameters
    ----------
    session_factory : async_sessionmaker[AsyncSession]
        Factory for creating async DB sessions.
    model_class : type, optional
        ORM model class to use (default: ``ChunkModel`` for 768d).
        Pass ``ChunkSpacyModel`` to operate on the 300d table.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        model_class: type = ChunkModel,
    ):
        self._session_factory = session_factory
        self._model = model_class

    async def insert_chunk(self, chunk: Chunk) -> int:
        return await self.insert_chunks([chunk])

    async def insert_chunks(self, chunks: list[Chunk]) -> int:
        async with self._session_factory() as session:
            models = [
                self._model(
                    snippet=chunk.content,
                    embedding=chunk.embeddings,
                    page=chunk.page or 1,
                )
                for chunk in chunks
            ]
            session.add_all(models)
            await session.commit()
            return len(models)

    async def search_similar(self, query_embedding: list[float], limit: int) -> list[ChunkResult]:
        async with self._session_factory() as session:
            stmt = (
                select(
                    self._model.snippet,
                    self._model.page,
                    self._model.embedding.cosine_distance(query_embedding).label("distance"),
                )
                .order_by("distance")
                .limit(limit)
            )
            rows = (await session.execute(stmt)).fetchall()
            return [
                ChunkResult(snippet=row.snippet, page=row.page, distance=row.distance)
                for row in rows
            ]

    async def count_chunks(self) -> int:
        async with self._session_factory() as session:
            result = await session.scalar(select(func.count()).select_from(self._model))
            return result or 0

    async def delete_all(self) -> None:
        async with self._session_factory() as session:
            await session.execute(delete(self._model))
            await session.commit()
