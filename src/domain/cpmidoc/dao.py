from domain.cpmidoc.models import CPMIDocPage
from psycopg_pool import ConnectionPool

class CPMIDocDao:
    def __init__(self, pool: ConnectionPool):
        self.pool: ConnectionPool = pool

    def delete_docs(self):
        """
        For setup/teardown
        """
        pass

    def get_count(self):
        pass

    def insert_doc(self, doc: list[CPMIDocPage]):
        pass
