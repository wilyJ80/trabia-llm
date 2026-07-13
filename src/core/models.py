"""Domain models for the RAG application."""

from typing import Literal

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


class ExtractedDocument(BaseModel):
    """Structured extraction result for Project 2 workflows."""

    document_type: str | None = Field(
        default=None,
        description="Tipo do documento analisado",
    )
    title: str | None = Field(
        default=None,
        description="Titulo ou identificador principal do documento",
    )
    main_event: str | None = Field(
        default=None,
        description="Evento, assunto ou objeto central do documento",
    )
    dates: list[str] = Field(
        default_factory=list,
        description="Datas relevantes identificadas no texto",
    )
    actors: list[str] = Field(
        default_factory=list,
        description="Pessoas ou agentes citados",
    )
    organizations: list[str] = Field(
        default_factory=list,
        description="Orgaos, instituicoes ou empresas citadas",
    )
    facts: list[str] = Field(
        default_factory=list,
        description="Fatos objetivos extraidos do documento",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Evidencias, trechos ou elementos que sustentam os fatos",
    )
    categories: list[str] = Field(
        default_factory=list,
        description="Categorias, temas ou classificacoes aplicaveis",
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="Fontes ou paginas usadas para sustentar a extracao",
    )
    missing_required_fields: list[str] = Field(
        default_factory=list,
        description="Campos obrigatorios ausentes ou insuficientes",
    )
    inferred_fields: list[str] = Field(
        default_factory=list,
        description="Campos preenchidos por regras locais, sem confirmacao do LLM",
    )
    validation_status: Literal["valid", "partial", "invalid"] = Field(
        default="partial",
        description="Resultado da validacao dos campos obrigatorios",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Problemas encontrados ao validar ou interpretar a resposta",
    )
    confidence: Literal["alta", "media", "baixa"] = Field(
        default="baixa",
        description="Confianca estimada com base na completude e nas fontes",
    )
