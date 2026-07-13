"""Pydantic schemas for the Extract endpoint."""

from pydantic import BaseModel, Field

from core.models import ExtractedDocument


class ExtractResponse(BaseModel):
    """Response body for POST /api/extract."""

    extraction: ExtractedDocument = Field(description="Dados estruturados extraidos")
    context_chunks_used: int = Field(
        default=0,
        description="Quantidade de chunks recuperados para apoio via RAG",
    )
    embedder_used: str = Field(default="openai", description="Embedder usado na recuperacao")
    params_used: dict = Field(
        default_factory=dict,
        description="Parametros usados na extracao",
    )
