import psycopg_pool
from domain.cpmidoc.models import CPMIDocPage
from psycopg_pool import ConnectionPool

class CPMIDocDao:
    def __init__(self, pool: ConnectionPool):
        self.pool: ConnectionPool = pool

    def delete_docs(self):
        """
        For setup/teardown
        """
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                sql = """
                DELETE FROM chunk
                """
                cur.execute(sql)
            conn.commit()

    def get_count(self):
        pass

    def insert_doc(self, doc: list[CPMIDocPage]):
        pass
