"""RAGService: orchestrates retrieval and generation with dependency injection."""

from tqdm import tqdm

from core.models import AIAnswer, Chunk
from core.port.embedder_port import EmbedderPort
from core.port.llm_port import LLMPort
from core.port.repository_port import RepositoryPort
from core.prompt import build_rag_prompt


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

        # 3. Format snippets with clear page markers
        snippets = [f"--- Trecho da página {r.page} ---\n{r.snippet}" for r in results]

        # 4. Build the prompt
        prompt = build_rag_prompt(question, snippets)

        # 5. Ask the LLM
        return await self._llm.ask(prompt)

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

            # Store each chunk immediately
            for chunk, emb in zip(batch, embeddings):
                chunk.embeddings = emb
                await self._repository.insert_chunk(chunk)

    async def chunk_count(self) -> int:
        """Return the total number of stored chunks."""
        return await self._repository.count_chunks()
