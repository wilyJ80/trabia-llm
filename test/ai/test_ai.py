from settings import Settings
from ai.llm import LLM
def test_ai():
    # TODO: AI answers
    settings: Settings = Settings()
    llm: LLM = LLM(
        settings.GOOGLE_API_KEY, settings.CHAT_MODEL
    )
    response: str = llm.ask('hello!')
    assert response is not None
    assert len(response) > 0
    # TODO: Structured output
    # TODO: Return grounded tool info
