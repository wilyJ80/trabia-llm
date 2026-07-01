from ingest.loader import Loader
from ingest.chunker import Chunker
from ingest.embedder import Embedder
from domain.cpmidoc.models import CPMIDocPage
from domain.cpmidoc.dao import CPMIDocDao
from psycopg_pool import ConnectionPool
from settings import Settings

def test_ingest():
    # INFO: Load data source
    filepath: str = 'data/relatorio-cpmi-versao-consolidada_231017_100010.pdf'
    loader: Loader = Loader()
    content: list[CPMIDocPage] = loader.load(filepath)
    assert content is not None
    assert isinstance(content, list)
    assert all(isinstance(page, CPMIDocPage) for page in content)
    assert len(content) > 0

    # INFO: get only part of the content to speed up tests
    content = content[:5]

    # INFO: chop chunks
    chunker: Chunker = Chunker()
    chunks: list[CPMIDocPage] = chunker.chunk(content)
    assert chunks is not None
    assert isinstance(chunks, list)
    assert all(isinstance(page, CPMIDocPage) for page in chunks)
    assert len(chunks) > 0
    print(len(chunks))

    # INFO: generate embeddings
    embedder: Embedder = Embedder()
    embedded_chunks: list[CPMIDocPage] = embedder.embed(chunks)
    assert embedded_chunks is not None
    assert isinstance(embedded_chunks, list)
    assert all(isinstance(page, CPMIDocPage) for page in embedded_chunks)
    assert len(embedded_chunks) > 0

    # INFO: db setup
    settings: Settings = Settings()
    pool: ConnectionPool = ConnectionPool(
        conninfo=settings.DAO_URL(), min_size=1, max_size=10, open=False
    )
    pool.open()
    dao: CPMIDocDao = CPMIDocDao(pool)
    assert dao.select_count() == 0

    # INFO: store content
    for chunk in embedded_chunks:
        dao.insert_doc(chunk)

    assert dao.select_count() > 0
