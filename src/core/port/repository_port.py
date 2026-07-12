"""Port (interface) for the vector database repository adapter."""

from abc import ABC, abstractmethod

from core.models import Chunk, ChunkResult


class RepositoryPort(ABC):
    """Interface for storing and querying document chunks."""

    @abstractmethod
    async def insert_chunk(self, chunk: Chunk) -> int:
        """Store a chunk with its embedding vector."""
        ...

    @abstractmethod
    async def search_similar(self, query_embedding: list[float], limit: int) -> list[ChunkResult]:
        """Find the most similar chunks to a query embedding."""
        ...

    @abstractmethod
    async def count_chunks(self) -> int:
        """Return the total number of stored chunks."""
        ...

    @abstractmethod
    async def delete_all(self) -> None:
        """Remove all chunks (for testing/cleanup)."""
        ...
