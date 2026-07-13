"""Integration test: full ingestion pipeline + query using SQLAlchemy ORM."""

import pytest

from core.service import RAGService
from infra.database import create_engine_and_session
from infra.embedder_openai import OpenAIEmbedder
from infra.llm_openai import OpenAILLM
from infra.repository import PgVectorRepository
from ingest.chunker import TextChunker
from ingest.loader import PDFLoader
from settings import Settings


@pytest.mark.asyncio
async def test_full_ingest_and_query():
    settings = Settings()  # type: ignore[call-arg]

    async_dsn = settings.DAO_URL().replace("postgresql://", "postgresql+asyncpg://")
    engine, session_factory = create_engine_and_session(async_dsn)

    repo = PgVectorRepository(session_factory)

    try:
        await repo.delete_all()

        # Load just the first 3 pages to speed up the test
        loader = PDFLoader()
        pages = loader.load("data/relatorio-cpmi-versao-consolidada_231017_100010.pdf")
        pages = pages[:3]

        chunker = TextChunker()
        chunks = chunker.chunk(pages)

        embedder = OpenAIEmbedder(
            model=settings.EMBED_MODEL,
            base_url=settings.EMBED_BASE_URL,
            api_key=settings.EMBED_API_KEY,
        )
        for chunk in chunks:
            chunk.embeddings = await embedder.embed_text(chunk.content)
            await repo.insert_chunk(chunk)

        assert await repo.count_chunks() > 0

        llm = OpenAILLM(
            model=settings.LLM_MODEL,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
        )
        service = RAGService(embedder=embedder, repository=repo, llm=llm)
        answer = await service.query("Do que se trata o relatório?", top_k=3)
        assert answer is not None
        assert len(answer.content) > 0
        assert isinstance(answer.sources, list)

    finally:
        await repo.delete_all()

    await engine.dispose()
