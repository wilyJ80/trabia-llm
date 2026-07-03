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

    # INFO: AI answers with structured output and grounded info
    settings: Settings = Settings()
    llm: LLM = LLM(
        settings.GOOGLE_API_KEY, settings.CHAT_MODEL
    )

    # INFO: Manual question step (vector search won't be a tool)
    service: CPMIDocService = CPMIDocService(pool)
    query: str = input("> ")
    search_results: list[str] = service.get_from_knowledge_base(query, 5)
    assert search_results is not None
    assert len(search_results) > 0
    prompt: str = f"""
    <system>
    Responda o usuário com base no contexto retornado.
    </system>
    <context>
    {"\n\n".join(search_results)}
    </context>
    <user>
    Do que se trata a base de conhecimento apresentada?
    </user>
    """

    response: AIAnswer = llm.ask(prompt)
    print(response)

if __name__ == "__main__":
    main()
