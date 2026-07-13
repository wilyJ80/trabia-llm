"""OpenAI-compatible embedding adapter — implements EmbedderPort using the OpenAI Python client.

Works with any provider that exposes an OpenAI-compatible embeddings endpoint:
- Ollama (local) — http://localhost:11434/v1
- OpenAI — https://api.openai.com/v1
- etc.
"""

from openai import AsyncOpenAI

from core.port.embedder_port import EmbedderPort


class OpenAIEmbedder(EmbedderPort):
    """Text embedder that uses any OpenAI-compatible embeddings API.

    Batched calls (``embed_texts``) send all texts in a single request,
    significantly reducing HTTP overhead.
    """

    def __init__(
        self,
        model: str = "nomic-embed-text:latest",
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        batch_size: int = 10,
    ):
        self._model = model
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self.batch_size = batch_size

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts in batch."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        # The OpenAI API returns results in the same order as the input
        return [item.embedding for item in response.data]

    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector for a query string."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=query,
        )
        return response.data[0].embedding
