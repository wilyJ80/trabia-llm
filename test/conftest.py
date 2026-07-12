from settings import Settings
import pytest
from domain.cpmidoc.dao import CPMIDocDao
from psycopg_pool import ConnectionPool

@pytest.fixture(autouse=True)
def cleanup():
    settings: Settings = Settings()
    pool: ConnectionPool = ConnectionPool(
        conninfo=settings.DAO_URL(), min_size=1, max_size=10, open=False
    )
    pool.open()
    dao: CPMIDocDao = CPMIDocDao(pool)
    dao.delete_docs()
    yield
    dao.delete_docs()
