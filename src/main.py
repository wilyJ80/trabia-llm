from psycopg_pool import ConnectionPool

from ai.llm import LLM
from ai.models import AIAnswer
from domain.cpmidoc.service import CPMIDocService
from settings import Settings


def main():
    # INFO: db setup
    settings: Settings = Settings()
    pool: ConnectionPool = ConnectionPool(
        conninfo=settings.DAO_URL(), min_size=1, max_size=10, open=False
    )
    pool.open()

    # INFO: AI answers with structured output and grounded info
    settings: Settings = Settings()
    llm: LLM = LLM(settings.GOOGLE_API_KEY, settings.CHAT_MODEL)

    # INFO: Manual question step (vector search won't be a tool)
    service: CPMIDocService = CPMIDocService(pool)
    query: str = input("> ")
    search_results: list[str] = service.get_from_knowledge_base(query, 5)
    assert search_results is not None
    assert len(search_results) > 0
    prompt: str = f"""
    <system>
    O contexto a seguir vem de busca semântica.
    Responda o usuário com base no contexto retornado.
    Há a possibilidade do contexto não ser relevante,
    dado que vem de uma busca semântica direta.
    </system>
    <context>
    {"\n\n".join(search_results)}
    </context>
    <user>
    {query}
    </user>
    """

    response: AIAnswer | None = llm.ask(prompt)
    print(response) if response else print("[ERROR] Could not ask LLM")


if __name__ == "__main__":
    main()
