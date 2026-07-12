"""Pydantic schemas for the Ingest and Health endpoints."""

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    """Response body for POST /api/ingest."""

    chunks_stored: int = Field(..., description="Total de chunks armazenados")
    message: str = Field(..., description="Mensagem de status")
    params_used: dict = Field(
        default_factory=dict,
        description="Parâmetros usados na ingestão",
    )


class HealthResponse(BaseModel):
    """Response body for GET /api/health."""

    status: str = Field(default="ok", description="Status da aplicação")
    chunks_count: int = Field(default=0, description="Total de chunks no banco")
    llm_connected: bool = Field(default=False, description="Se o provedor de LLM está acessível")
