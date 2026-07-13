"""FastAPI route for structured document extraction."""

import os
import tempfile
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.dependencies import EMBEDDER_OPENAI, build_service, get_session_factory
from api.schemas.extract import ExtractResponse
from ingest.loader import PDFLoader

router = APIRouter(prefix="/api", tags=["extract"])


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    file: UploadFile | None = File(
        default=None,
        description="Arquivo PDF para extracao estruturada",
    ),
    text: str = Form(
        default="",
        description="Texto bruto para extracao estruturada",
    ),
    top_k: int = Form(
        default=5,
        ge=0,
        le=50,
        description="Quantidade de chunks recuperados como contexto externo",
    ),
    embedder: Literal["openai", "spacy"] = Form(
        default=EMBEDDER_OPENAI,
        description="Tipo de embedding usado na recuperacao: 'openai' ou 'spacy'",
    ),
    session_factory=Depends(get_session_factory),
) -> ExtractResponse:
    """Extract structured fields from a PDF or raw text using LLM validation."""
    if file is None and not text.strip():
        raise HTTPException(status_code=400, detail="Envie um PDF, um texto, ou ambos.")

    document_parts: list[str] = []
    source_names: list[str] = []
    tmp_path = None

    try:
        if text.strip():
            document_parts.append(text.strip())
            source_names.append("text")

        if file is not None:
            if not file.filename or not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail="Apenas arquivos PDF sao aceitos.")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name

            pages = PDFLoader().load(tmp_path)
            pdf_text = "\n\n".join(f"[pagina {page.page or 1}]\n{page.content}" for page in pages)
            if pdf_text.strip():
                document_parts.append(pdf_text)
            source_names.append(file.filename)

        document_text = "\n\n".join(document_parts).strip()
        if not document_text:
            raise HTTPException(status_code=400, detail="Nao foi possivel extrair texto do envio.")

        service = build_service(session_factory, embedder_type=embedder)
        extraction, context_chunks_used = await service.extract(document_text, top_k=top_k)

        return ExtractResponse(
            extraction=extraction,
            context_chunks_used=context_chunks_used,
            embedder_used=embedder,
            params_used={
                "sources": source_names,
                "top_k": top_k,
                "embedder": embedder,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
