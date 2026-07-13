"""Text chunker using RecursiveCharacterTextSplitter from LangChain."""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from core.models import Chunk


class TextChunker:
    """Split page-level text into smaller overlapping chunks."""

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk(self, pages: list[Chunk]) -> list[Chunk]:
        """Split each page into smaller chunks."""
        all_chunks: list[Chunk] = []
        for page in tqdm(pages, desc="Chunking pages"):
            splits: list[str] = self._splitter.split_text(page.content)
            for split in splits:
                all_chunks.append(Chunk(content=split, page=page.page, embeddings=[]))
        return all_chunks
