from ingest.loader import Loader
from ingest.chunker import Chunker
from ingest.embedder import Embedder
from domain.cpmidoc.models import CPMIDocPage
from domain.cpmidoc.dao import CPMIDocDao
from psycopg_pool import ConnectionPool
from settings import Settings
from tqdm import tqdm

def main():
    print('[INFO] Loading...')
    filepath: str = 'data/relatorio-cpmi-versao-consolidada_231017_100010.pdf'
    loader: Loader = Loader()
    content: list[CPMIDocPage] = loader.load(filepath)
    chunker: Chunker = Chunker()
    print('[INFO] Chunking...')
    chunks: list[CPMIDocPage] = chunker.chunk(content)
    print('[INFO] Loading embedding model...')
    embedder: Embedder = Embedder()
    print('[INFO] Embedding...')
    embedded_chunks: list[CPMIDocPage] = embedder.embed(chunks)

    # INFO: Storage
    print('[INFO] Preparing DB...')
    settings: Settings = Settings()
    pool: ConnectionPool = ConnectionPool(
        conninfo=settings.DAO_URL(), min_size=1, max_size=10, open=False
    )
    pool.open()
    dao: CPMIDocDao = CPMIDocDao(pool)
    print('[INFO] Storing...')
    for chunk in tqdm(embedded_chunks):
        dao.insert_doc(chunk)

    print("[INFO] Finished.")

if __name__ == "__main__":
    main()
