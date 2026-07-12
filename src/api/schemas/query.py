"""Pydantic schemas for the Query endpoint."""

from pydantic import BaseModel, Field

from core.models import AIAnswer


class QueryRequest(BaseModel):
    """Request body for POST /api/query."""

    question: str = Field(..., min_length=1, description="Pergunta do usuário")
    top_k: int = Field(default=5, ge=1, le=50, description="Número de trechos a recuperar")
    embedder: str = Field(
        default="openai",
        description="Tipo de embedding usado na busca: 'openai' (768d, padrão) ou 'spacy' (300d)",
    )


class QueryResponse(BaseModel):
    """Response body for POST /api/query."""

    answer: AIAnswer
    embedder_used: str = Field(default="openai", description="Embedder utilizado nesta consulta")
