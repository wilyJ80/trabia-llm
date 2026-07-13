"""FastAPI dependency providers for dependency injection."""

from functools import lru_cache

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.service import RAGService
from infra.embedder_openai import OpenAIEmbedder
from infra.embedder_spacy import SpacyEmbedder
from infra.llm_openai import OpenAILLM
from infra.models import ChunkModel, ChunkSpacyModel
from infra.repository import PgVectorRepository
from settings import Settings

EMBEDDER_OPENAI = "openai"
EMBEDDER_SPACY = "spacy"


@lru_cache(maxsize=1)
def get_spacy_embedder() -> SpacyEmbedder:
    """Load the large spaCy model once per API process."""
    return SpacyEmbedder()


def build_service(
    session_factory: async_sessionmaker[AsyncSession],
    embedder_type: str = EMBEDDER_OPENAI,
) -> RAGService:
    """Build a wired RAGService for the given embedder type.

    Parameters
    ----------
    session_factory : async_sessionmaker[AsyncSession]
        Factory for DB sessions.
    embedder_type : str
        ``"openai"`` (default, 768d) or ``"spacy"`` (300d).
        The corresponding table (chunk or chunk_spacy) is used
        automatically.
    """
    settings = Settings()  # type: ignore[call-arg]

    # ── Embedder ──────────────────────────────────────────────────
    if embedder_type == EMBEDDER_SPACY:
        embedder = get_spacy_embedder()
    else:
        embedder = OpenAIEmbedder(
            model=settings.EMBED_MODEL,
            base_url=settings.EMBED_BASE_URL,
            api_key=settings.EMBED_API_KEY,
        )

    # ── Repository (auto-selects the right table) ─────────────────
    model_class = ChunkSpacyModel if embedder_type == EMBEDDER_SPACY else ChunkModel
    repository = PgVectorRepository(session_factory, model_class=model_class)

    # ── LLM (shared, independent of embedder) ─────────────────────
    llm = OpenAILLM(
        model=settings.LLM_MODEL,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
    )

    return RAGService(embedder=embedder, repository=repository, llm=llm)


def get_service(request: Request) -> RAGService:
    """Retrieve the default (OpenAI) RAGService from the application state."""
    return request.app.state.service


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    """Retrieve the session factory from the application state.

    Used by routes that need to create a temporary service with
    a different embedder.
    """
    return request.app.state.session_factory
