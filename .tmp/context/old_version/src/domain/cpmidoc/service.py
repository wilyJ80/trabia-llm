from settings import Settings
from ingest.embedder import Embedder
from psycopg_pool import ConnectionPool
from domain.cpmidoc.dao import CPMIDocDao
from domain.cpmidoc.models import CPMIDocResult

class CPMIDocService:
    def __init__(self, pool: ConnectionPool):
        self.dao: CPMIDocDao = CPMIDocDao(pool)

    def get_from_knowledge_base(self, query: str, k: int) -> list[str]:
        """
        description
        """
        embedder: Embedder = Embedder()
        embedded_query: list[int | float] = embedder.embed_query(query)
        results: list[CPMIDocResult] = self.dao.select_similarity(embedded_query, k)
        return [
            f"""
            <snippet>{result.snippet}</snippet>
            <page>{result.page}</page>
            """
            for result in results
        ]
