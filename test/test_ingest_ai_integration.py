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

def test_ai_integration():
    # INFO: Load data source
    filepath: str = 'data/relatorio-cpmi-versao-consolidada_231017_100010.pdf'
    loader: Loader = Loader()
    content: list[CPMIDocPage] = loader.load(filepath)
    assert content is not None
    assert isinstance(content, list)
    assert all(isinstance(page, CPMIDocPage) for page in content)
    assert len(content) > 0

    # INFO: get only part of the content to speed up tests
    content = content[:15]

    # INFO: chop chunks
    chunker: Chunker = Chunker()
    chunks: list[CPMIDocPage] = chunker.chunk(content)
    assert chunks is not None
    assert isinstance(chunks, list)
    assert all(isinstance(page, CPMIDocPage) for page in chunks)
    assert len(chunks) > 0

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

    # INFO: check if query works
    embedded_query: list[int | float] = embedder.embed_query('Congresso')
    result: list[CPMIDocResult] = dao.select_similarity(embedded_query, settings.K)
    assert result is not None
    assert len(result) > 0

    # INFO: AI answers with structured output and grounded info
    settings: Settings = Settings()
    llm: LLM = LLM(
        settings.GOOGLE_API_KEY, settings.CHAT_MODEL
    )

    # INFO: Manual question step (vector search won't be a tool)
    service: CPMIDocService = CPMIDocService(pool)
    query: str = 'Congresso'
    search_results: list[str] = service.get_from_knowledge_base(query, 5)
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
    assert response is not None
    assert len(response.content) > 0
    assert isinstance(response, AIAnswer)

    print(response) # INFO: for debugging
