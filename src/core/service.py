"""RAGService: orchestrates retrieval, generation and extraction."""

import json
import re

from pydantic import ValidationError
from tqdm import tqdm

from core.models import AIAnswer, Chunk, ExtractedDocument
from core.port.embedder_port import EmbedderPort
from core.port.llm_port import LLMPort
from core.port.repository_port import RepositoryPort
from core.prompt import build_extraction_prompt, build_extraction_repair_prompt, build_rag_prompt

REQUIRED_EXTRACTION_FIELDS = ("document_type", "title", "main_event", "facts")
MAX_EXTRACTION_CHARS = 24000
MAX_RETRIEVAL_QUERY_CHARS = 3000


class RAGService:
    """Orchestrates the RAG pipeline: embed query → search → build prompt → LLM."""

    def __init__(
        self,
        embedder: EmbedderPort,
        repository: RepositoryPort,
        llm: LLMPort,
    ):
        self._embedder = embedder
        self._repository = repository
        self._llm = llm

    async def query(self, question: str, top_k: int = 5) -> AIAnswer:
        """Run the full RAG pipeline for a user question."""
        # 1. Embed the query
        query_vector = await self._embedder.embed_query(question)

        # 2. Retrieve relevant chunks
        results = await self._repository.search_similar(query_vector, top_k)

        # 3. Check if any relevant context was found
        if not results:
            raise ValueError(
                "Nenhum trecho relevante encontrado na base vetorial para este embedder. "
                "Ingira um PDF primeiro ou selecione 'Sem RAG (so LLM)' para "
                "consultar o modelo diretamente."
            )

        # 4. Format snippets with clear page markers
        snippets = [f"--- Trecho da página {r.page} ---\n{r.snippet}" for r in results]

        # 5. Build the prompt
        prompt = build_rag_prompt(question, snippets)

        # 6. Ask the LLM
        return await self._llm.ask(prompt)

    async def extract(self, document_text: str, top_k: int = 5) -> tuple[ExtractedDocument, int]:
        """Extract structured fields from a document, with optional RAG support."""
        document_text = document_text.strip()
        if not document_text:
            extraction = ExtractedDocument(
                missing_required_fields=list(REQUIRED_EXTRACTION_FIELDS),
                validation_status="invalid",
                validation_errors=["Documento vazio ou sem texto extraivel."],
                confidence="baixa",
            )
            return extraction, 0

        results = []
        if top_k > 0:
            retrieval_query = self._build_retrieval_query(document_text)
            query_vector = await self._embedder.embed_query(retrieval_query)
            results = await self._repository.search_similar(query_vector, top_k)

        document_excerpt = self._select_document_excerpt(document_text)
        snippets = [f"--- Trecho da pagina {r.page} ---\n{r.snippet}" for r in results]
        prompt = build_extraction_prompt(document_excerpt, snippets)
        raw_response = await self._llm.ask_text(prompt, max_tokens=4096, json_mode=True)

        extraction = self._parse_extraction(raw_response)
        if self._needs_json_repair(extraction):
            repair_prompt = build_extraction_repair_prompt(raw_response)
            repaired_response = await self._llm.ask_text(
                repair_prompt,
                max_tokens=2048,
                json_mode=True,
            )
            extraction = self._parse_extraction(repaired_response)

        extraction = self._validate_extraction(extraction)
        extraction = self._apply_extraction_fallbacks(document_excerpt, extraction)
        return extraction, len(results)

    async def embed_and_store(self, chunks: list[Chunk]) -> None:
        """Embed chunks in batches, then store each one incrementally.

        Uses the embedder's batch_size to process multiple texts in a
        single API call, significantly reducing HTTP overhead.
        Each chunk is stored immediately after its batch is embedded,
        so partial progress is preserved.
        """
        batch_size = getattr(self._embedder, "batch_size", 1)

        for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]

            # Batch embed all texts in one call
            embeddings = await self._embedder.embed_texts(texts)

            embedded_chunks: list[Chunk] = []
            for chunk, emb in zip(batch, embeddings):
                embedded_chunks.append(chunk.model_copy(update={"embeddings": emb}))
            await self._repository.insert_chunks(embedded_chunks)

    async def chunk_count(self) -> int:
        """Return the total number of stored chunks."""
        return await self._repository.count_chunks()

    async def clear_collection(self) -> None:
        """Remove all chunks from the repository selected for this service."""
        await self._repository.delete_all()

    @staticmethod
    def _select_document_excerpt(document_text: str) -> str:
        """Select page blocks across a long document instead of keeping only its beginning."""
        if len(document_text) <= MAX_EXTRACTION_CHARS:
            return document_text

        page_blocks = re.split(r"(?=\[pagina \d+\])", document_text, flags=re.IGNORECASE)
        page_blocks = [block.strip() for block in page_blocks if block.strip()]
        if len(page_blocks) < 2:
            segment_size = MAX_EXTRACTION_CHARS // 3
            middle_start = max((len(document_text) - segment_size) // 2, segment_size)
            return "\n\n[trecho intermediario]\n".join(
                (
                    document_text[:segment_size],
                    document_text[middle_start : middle_start + segment_size],
                    document_text[-segment_size:],
                )
            )

        selected: list[str] = []
        selected_indexes: set[int] = set()
        target_blocks = min(24, len(page_blocks))
        separator_chars = 2 * (target_blocks - 1)
        chars_per_block = (MAX_EXTRACTION_CHARS - separator_chars) // target_blocks
        for position in range(target_blocks):
            index = round(position * (len(page_blocks) - 1) / max(target_blocks - 1, 1))
            if index in selected_indexes:
                continue
            selected.append(page_blocks[index][:chars_per_block])
            selected_indexes.add(index)

        return "\n\n".join(selected)

    @staticmethod
    def _build_retrieval_query(document_text: str) -> str:
        """Build a bounded query with content from the start, middle and end."""
        if len(document_text) <= MAX_RETRIEVAL_QUERY_CHARS:
            return document_text

        segment_size = MAX_RETRIEVAL_QUERY_CHARS // 3
        middle_start = (len(document_text) - segment_size) // 2
        return "\n".join(
            (
                document_text[:segment_size],
                document_text[middle_start : middle_start + segment_size],
                document_text[-segment_size:],
            )
        )

    @staticmethod
    def _parse_extraction(raw_response: str) -> ExtractedDocument:
        """Parse the LLM JSON response into an ExtractedDocument."""
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
            if not match:
                return ExtractedDocument(
                    missing_required_fields=list(REQUIRED_EXTRACTION_FIELDS),
                    validation_status="invalid",
                    validation_errors=["LLM nao retornou um objeto JSON."],
                    confidence="baixa",
                )
            try:
                payload = json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                return ExtractedDocument(
                    missing_required_fields=list(REQUIRED_EXTRACTION_FIELDS),
                    validation_status="invalid",
                    validation_errors=[f"JSON invalido retornado pelo LLM: {exc.msg}."],
                    confidence="baixa",
                )

        normalized_payload = RAGService._normalize_extraction_payload(payload)

        try:
            return ExtractedDocument.model_validate(normalized_payload)
        except ValidationError as exc:
            return ExtractedDocument(
                missing_required_fields=list(REQUIRED_EXTRACTION_FIELDS),
                validation_status="invalid",
                validation_errors=[error["msg"] for error in exc.errors()],
                confidence="baixa",
            )

    @staticmethod
    def _needs_json_repair(extraction: ExtractedDocument) -> bool:
        """Return True when parsing failed before schema validation could run."""
        return extraction.validation_status == "invalid" and any(
            "JSON invalido" in error or "LLM nao retornou" in error
            for error in extraction.validation_errors
        )

    @staticmethod
    def _normalize_extraction_payload(payload: object) -> dict:
        """Normalize common LLM variations before Pydantic validation."""
        if not isinstance(payload, dict):
            return {}

        aliases = {
            "tipo_documento": "document_type",
            "tipo": "document_type",
            "titulo": "title",
            "evento_principal": "main_event",
            "assunto_principal": "main_event",
            "evento": "main_event",
            "datas": "dates",
            "atores": "actors",
            "pessoas": "actors",
            "organizacoes": "organizations",
            "organizações": "organizations",
            "orgaos": "organizations",
            "órgãos": "organizations",
            "instituicoes": "organizations",
            "instituições": "organizations",
            "fatos": "facts",
            "evidencias": "evidence",
            "evidências": "evidence",
            "categorias": "categories",
            "fontes": "sources",
            "confianca": "confidence",
            "confiança": "confidence",
        }

        normalized = dict(payload)
        for source_key, target_key in aliases.items():
            if target_key not in normalized and source_key in payload:
                normalized[target_key] = payload[source_key]

        for field in ("document_type", "title", "main_event"):
            value = normalized.get(field)
            if value is not None and not isinstance(value, str):
                normalized[field] = RAGService._stringify(value)

        for field in ("dates", "actors", "organizations", "facts", "evidence", "categories"):
            normalized[field] = RAGService._string_list(normalized.get(field))

        sources = normalized.get("sources") or []
        if not isinstance(sources, list):
            sources = [sources]
        normalized["sources"] = [RAGService._normalize_source(source) for source in sources]

        confidence = normalized.get("confidence")
        if confidence is None:
            normalized["confidence"] = "baixa"
        elif isinstance(confidence, str):
            confidence = confidence.lower().strip()
            if confidence in {"alta", "alto", "high"}:
                normalized["confidence"] = "alta"
            elif confidence in {"media", "média", "medio", "médio", "medium"}:
                normalized["confidence"] = "media"
            else:
                normalized["confidence"] = "baixa"

        return normalized

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [RAGService._stringify(item) for item in value if item is not None]
        return [RAGService._stringify(value)]

    @staticmethod
    def _normalize_source(source: object) -> dict:
        if isinstance(source, dict):
            claim = (
                source.get("claim")
                or source.get("fato")
                or source.get("trecho")
                or source.get("descricao")
                or source.get("descrição")
                or "Fonte citada"
            )
            page = source.get("page") or source.get("pagina") or source.get("página") or 0
        else:
            claim = source
            page = 0

        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 0

        return {"claim": RAGService._stringify(claim), "page": page}

    @staticmethod
    def _stringify(value: object) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in (
                "claim",
                "fato",
                "name",
                "nome",
                "title",
                "titulo",
                "descrição",
                "descricao",
                "value",
            ):
                if key in value and value[key] is not None:
                    return RAGService._stringify(value[key])
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _apply_extraction_fallbacks(
        document_text: str,
        extraction: ExtractedDocument,
    ) -> ExtractedDocument:
        """Fill obvious missing fields using deterministic document-text rules."""
        lines = [
            line.strip()
            for line in document_text.splitlines()
            if line.strip() and not line.strip().lower().startswith("[pagina ")
        ]
        full_text = "\n".join(lines)

        updates: dict = {}

        if not extraction.title and lines:
            updates["title"] = lines[0][:180]

        if not extraction.document_type:
            first_lines = " ".join(lines[:5]).lower()
            if "relatório" in first_lines or "relatorio" in first_lines:
                updates["document_type"] = "relatorio"
            elif "ata" in first_lines:
                updates["document_type"] = "ata"
            elif "edital" in first_lines:
                updates["document_type"] = "edital"
            elif "notícia" in first_lines or "noticia" in first_lines:
                updates["document_type"] = "noticia"
            else:
                updates["document_type"] = "documento"

        if not extraction.main_event:
            problem_match = re.search(
                r"defini[çc][aã]o do problema\s+(.*?)(?:\n[A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{2,80}\n|$)",
                full_text,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if problem_match:
                updates["main_event"] = RAGService._first_sentence(problem_match.group(1))
            elif len(lines) > 1:
                updates["main_event"] = RAGService._first_sentence(" ".join(lines[1:4]))

        if not extraction.facts:
            fact_candidates = RAGService._sentence_candidates(full_text)
            updates["facts"] = fact_candidates[:3]

        updates["inferred_fields"] = list(
            dict.fromkeys([*extraction.inferred_fields, *updates.keys()])
        )
        return extraction.model_copy(update=updates)

    @staticmethod
    def _sentence_candidates(text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        return [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 40]

    @staticmethod
    def _first_sentence(text: str) -> str:
        candidates = RAGService._sentence_candidates(text)
        if candidates:
            return candidates[0][:240]
        return text.strip().replace("\n", " ")[:240]

    @staticmethod
    def _validate_extraction(extraction: ExtractedDocument) -> ExtractedDocument:
        """Validate required extraction fields and annotate the result."""
        missing: list[str] = []
        for field in REQUIRED_EXTRACTION_FIELDS:
            value = getattr(extraction, field)
            if field in extraction.inferred_fields or value is None or value == "" or value == []:
                missing.append(field)

        errors = list(extraction.validation_errors)
        for field in missing:
            message = f"Campo obrigatorio ausente ou insuficiente: {field}."
            if message not in errors:
                errors.append(message)

        if missing:
            status = "invalid" if len(missing) == len(REQUIRED_EXTRACTION_FIELDS) else "partial"
            confidence = "baixa" if status == "invalid" else extraction.confidence
        else:
            status = "valid"
            confidence = extraction.confidence

        return extraction.model_copy(
            update={
                "missing_required_fields": missing,
                "validation_status": status,
                "validation_errors": errors,
                "confidence": confidence,
            }
        )
