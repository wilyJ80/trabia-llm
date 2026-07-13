"""FastAPI route for the Query endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import (
    build_service,
    get_session_factory,
)
from api.schemas.query import QueryRequest, QueryResponse
from core.prompt import build_direct_prompt
from infra.llm_openai import OpenAILLM
from settings import Settings

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    session_factory=Depends(get_session_factory),
) -> QueryResponse:
    """Ask a question to the RAG system.

    The question is embedded with the chosen embedder, used for vector
    similarity search on the corresponding table, and the retrieved
    context is passed to the LLM for answer generation.

    Use ``embedder="openai"`` to query the main chunk table (768d),
    or ``embedder="spacy"`` to query the chunk_spacy table (300d).
    Use ``embedder="none"`` to query the LLM directly without RAG.
    """
    try:
        if body.embedder == "none":
            settings = Settings()  # type: ignore[call-arg]
            llm = OpenAILLM(
                model=settings.LLM_MODEL,
                base_url=settings.LLM_BASE_URL,
                api_key=settings.LLM_API_KEY,
            )
            prompt = build_direct_prompt(body.question)
            answer = await llm.ask(prompt)
            return QueryResponse(answer=answer, embedder_used="none")

        service = build_service(session_factory, embedder_type=body.embedder)
        answer = await service.query(body.question, top_k=body.top_k)
        return QueryResponse(answer=answer, embedder_used=body.embedder)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
