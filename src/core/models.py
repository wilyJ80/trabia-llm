"""Domain models for the RAG application."""

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A chunk of text extracted from the PDF, with embedding data."""

    content: str
    page: int | None
    embeddings: list[float]


class ChunkResult(BaseModel):
    """Result from a vector similarity search."""

    snippet: str
    page: int | None
    distance: float


class Source(BaseModel):
    """A source citation for an answer."""

    claim: str = Field(description="Informação encontrada")
    page: int = Field(description="Página associada")


class AIAnswer(BaseModel):
    """Structured output from the LLM."""

    content: str = Field(description="Sua resposta")
    sources: list[Source] = Field(description="Fontes da resposta encontradas")
