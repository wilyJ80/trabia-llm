from ingest.loader import Loader
from ingest.chunker import Chunker
from ingest.embedder import Embedder
from ingest.models import CPMIDocPage

def test_ingest():
    filepath: str = 'data/relatorio-cpmi-versao-consolidada_231017_100010.pdf'
    loader: Loader = Loader()
    content: list[CPMIDocPage] = loader.load(filepath)
    assert content is not None
    assert isinstance(content, list)
    assert all(isinstance(page, CPMIDocPage) for page in content)
    assert len(content) > 0

    chunker: Chunker = Chunker()
    chunks: list[CPMIDocPage] = chunker.chunk(content)
    assert chunks is not None
    assert isinstance(chunks, list)
    assert all(isinstance(page, CPMIDocPage) for page in chunks)
    assert len(chunks) > 0
    print(len(chunks))

    embedder: Embedder = Embedder()
    embedded_chunks: list[CPMIDocPage] = embedder.embed(chunks)
    assert embedded_chunks is not None
    assert isinstance(embedded_chunks, list)
    assert all(isinstance(page, CPMIDocPage) for page in embedded_chunks)
    assert len(embedded_chunks) > 0
