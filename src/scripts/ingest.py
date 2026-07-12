"""Manual ingestion script — run once to populate the vector database.

Usage:
    uv run python -m src.scripts.ingest
"""

import asyncio

from core.models import Chunk
from core.service import RAGService
from infra.database import create_engine_and_session
from infra.embedder_openai import OpenAIEmbedder
from infra.llm_openai import OpenAILLM
from infra.repository import PgVectorRepository
from ingest.chunker import TextChunker
from ingest.loader import PDFLoader
from settings import Settings


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    filepath = "data/relatorio-cpmi-versao-consolidada_231017_100010.pdf"

    print("[INFO] Loading PDF...")
    loader = PDFLoader()
    pages: list[Chunk] = loader.load(filepath)
    print(f"[INFO] Loaded {len(pages)} pages.")

    print("[INFO] Chunking...")
    chunker = TextChunker()
    chunks: list[Chunk] = chunker.chunk(pages)
    print(f"[INFO] Created {len(chunks)} chunks.")

    # ── Build service with incremental embed_and_store ────────────
    print("[INFO] Connecting to database...")
    async_dsn = settings.DAO_URL().replace("postgresql://", "postgresql+asyncpg://")
    engine, session_factory = create_engine_and_session(async_dsn)

    embedder = OpenAIEmbedder(
        model=settings.EMBED_MODEL,
        base_url=settings.EMBED_BASE_URL,
        api_key=settings.EMBED_API_KEY,
    )
    repository = PgVectorRepository(session_factory)
    llm = OpenAILLM(
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )
    service = RAGService(embedder=embedder, repository=repository, llm=llm)

    # embed_and_store is incremental: embeds + saves one by one
    print(f"[INFO] Embedding & storing {len(chunks)} chunks (incremental)...")
    await service.embed_and_store(chunks)

    total = await service.chunk_count()
    print(f"[INFO] Finished! {total} chunks stored in the database.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
