"""Tests for the PDF loading and chunking pipeline."""

from core.models import Chunk
from ingest.chunker import TextChunker
from ingest.loader import PDFLoader


def test_loader_returns_pages():
    filepath = "data/relatorio-cpmi-versao-consolidada_231017_100010.pdf"
    loader = PDFLoader()
    pages = loader.load(filepath)

    assert pages is not None
    assert isinstance(pages, list)
    assert len(pages) > 0
    assert all(isinstance(p, Chunk) for p in pages)
    assert all(p.page is not None for p in pages)
    assert pages[0].page == 1
    assert all(len(p.content) > 0 for p in pages)
    assert len(pages) == 1333


def test_chunker_creates_more_chunks_than_pages():
    filepath = "data/relatorio-cpmi-versao-consolidada_231017_100010.pdf"
    loader = PDFLoader()
    pages = loader.load(filepath)

    chunker = TextChunker()
    chunks = chunker.chunk(pages)

    assert chunks is not None
    assert isinstance(chunks, list)
    assert len(chunks) > len(pages)
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.page is not None for c in chunks)
    assert len(chunks) == 1533
