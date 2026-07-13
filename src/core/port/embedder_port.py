"""Port (interface) for the text embedder adapter."""

from abc import ABC, abstractmethod


class EmbedderPort(ABC):
    """Interface for generating text embeddings."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        ...

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts in batch.

        Batched calls are significantly faster than calling embed_text
        repeatedly due to reduced HTTP overhead and internal parallelism.
        """
        ...

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector for a query string."""
        ...
