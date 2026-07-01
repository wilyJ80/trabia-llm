from ingest.loader import Loader
from ingest.chunker import Chunker
from ingest.embedder import Embedder
from domain.cpmidoc.models import CPMIDocPage, CPMIDocResult
from domain.cpmidoc.dao import CPMIDocDao
from psycopg_pool import ConnectionPool
from settings import Settings
from ai.llm import LLM
from ai.models import AIAnswer
from domain.cpmidoc.service import CPMIDocService
from psycopg_pool import ConnectionPool

def main():
    # INFO: db setup
    settings: Settings = Settings()
    pool: ConnectionPool = ConnectionPool(
        conninfo=settings.DAO_URL(), min_size=1, max_size=10, open=False
    )
    pool.open()
    dao: CPMIDocDao = CPMIDocDao(pool)

    # INFO: query
    embedder: Embedder = Embedder()
    query: str = input("> ")
    embedded_query: list[int | float] = embedder.embed_query(query)
    result: list[CPMIDocResult] = dao.select_similarity(embedded_query, settings.K)

    print('\n\n==============\n\n'.join([r.snippet for r in result]))

if __name__ == "__main__":
    main()
