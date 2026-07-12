"""FastAPI routes for Ingest and Health endpoints."""

import os
import tempfile
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.dependencies import EMBEDDER_OPENAI, build_service, get_service, get_session_factory
from api.schemas.ingest import HealthResponse, IngestResponse
from core.service import RAGService
from ingest.chunker import TextChunker
from ingest.loader import PDFLoader

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(..., description="Arquivo PDF para ingestão"),
    chunk_size: int = Form(default=2000, ge=500, le=8000, description="Tamanho de cada chunk"),
    chunk_overlap: int = Form(default=200, ge=0, le=1000, description="Sobreposição entre chunks"),
    embedder: Literal["openai", "spacy"] = Form(
        default=EMBEDDER_OPENAI,
        description="Tipo de embedding: 'openai' (768d) ou 'spacy' (300d)",
    ),
    session_factory=Depends(get_session_factory),
) -> IngestResponse:
    """Upload a PDF document and run the full ingestion pipeline.

    The file is saved temporarily, processed (load → chunk → embed → store),
    and then removed. The ``chunk_size`` and ``chunk_overlap`` parameters
    allow experimenting with different chunking strategies, and ``embedder``
    lets you compare OpenAI-compatible vs spaCy embeddings.

    Usage:
        curl -X POST http://localhost:8000/api/ingest \
          -F "file=@documento.pdf" \
          -F "chunk_size=2000" \
          -F "chunk_overlap=200" \
          -F "embedder=openai"
    """
    # Validate file type by extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    tmp_path = None
    try:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        loader = PDFLoader()
        pages = loader.load(tmp_path)

        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = chunker.chunk(pages)

        # Build a service with the requested embedder
        service = build_service(session_factory, embedder_type=embedder)
        await service.embed_and_store(chunks)

        return IngestResponse(
            chunks_stored=len(chunks),
            message=f"Ingestão concluída: {len(chunks)} chunks armazenados de '{file.filename}'.",
            params_used={
                "filename": file.filename,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "embedder": embedder,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up the temporary file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/health", response_model=HealthResponse)
async def health(
    service: RAGService = Depends(get_service),
) -> HealthResponse:
    """Check application health status."""
    try:
        chunks = await service.chunk_count()
        return HealthResponse(status="ok", chunks_count=chunks, llm_connected=True)
    except Exception:
        return HealthResponse(status="error", chunks_count=0, llm_connected=False)
