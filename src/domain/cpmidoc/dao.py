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

    def select_count(self) -> int:
        """
        For test assertions
        """
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                sql = """
                SELECT COUNT(*)
                FROM chunk
                """
                row = cur.execute(sql).fetchone()
                return row[0] if row else 0

    def insert_doc(self, doc: CPMIDocPage) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                sql = """
                INSERT INTO chunk (
                    snippet, embedding, page
                )
                VALUES (
                %s, %s, %s
                )
                """
                cur.execute(
                    sql, (doc.content, doc.embeddings, doc.page,)
                )
                return cur.rowcount
