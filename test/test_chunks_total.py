from domain.cpmidoc.models import CPMIDocPage
from ingest.chunker import Chunker
from ingest.loader import Loader


def test_ai_integration():
    # INFO: Load data source
    filepath: str = "data/relatorio-cpmi-versao-consolidada_231017_100010.pdf"
    loader: Loader = Loader()
    content: list[CPMIDocPage] = loader.load(filepath)
    assert content is not None
    assert isinstance(content, list)
    assert all(isinstance(page, CPMIDocPage) for page in content)
    assert len(content) > 0

    assert len(content) == 1333

    # INFO: chop chunks
    chunker: Chunker = Chunker()
    chunks: list[CPMIDocPage] = chunker.chunk(content)
    assert chunks is not None
    assert isinstance(chunks, list)
    assert all(isinstance(page, CPMIDocPage) for page in chunks)
    assert len(chunks) > 0

    assert len(chunks) == 1533
