from psycopg.rows import class_row
import psycopg_pool
from domain.cpmidoc.models import CPMIDocPage, CPMIDocResult
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

    def select_similarity(self, query_embedding: list[float], limit: int) -> list[CPMIDocResult]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=class_row(CPMIDocResult)) as cur:
                sql = """
                SELECT snippet, page, embedding <=> %s::halfvec AS distance
                FROM chunk
                ORDER BY distance
                LIMIT %s;
                """
                cur.execute(sql, (query_embedding, limit,))
                docs: list[CPMIDocResult] = cur.fetchall()
                return docs
