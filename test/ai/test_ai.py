from settings import Settings
from ai.llm import LLM
from ai.models import AIAnswer
from domain.cpmidoc.service import CPMIDocService
from psycopg_pool import ConnectionPool

def test_ai():
    # INFO: AI answers with structured output and grounded info
    settings: Settings = Settings()
    llm: LLM = LLM(
        settings.GOOGLE_API_KEY, settings.CHAT_MODEL
    )

    # INFO: db setup
    settings: Settings = Settings()
    pool: ConnectionPool = ConnectionPool(
        conninfo=settings.DAO_URL(), min_size=1, max_size=10, open=False
    )
    pool.open()

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
    O que a base de conhecimento diz sobre o Congresso?
    </user>
    """

    response: AIAnswer = llm.ask(prompt)
    assert response is not None
    assert len(response.content) > 0
    assert isinstance(response, AIAnswer)

    print(response)
