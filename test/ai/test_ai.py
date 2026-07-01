from settings import Settings
from ai.llm import LLM
from ai.models import AIAnswer
def test_ai():
    # INFO: AI answers with structured output
    settings: Settings = Settings()
    llm: LLM = LLM(
        settings.GOOGLE_API_KEY, settings.CHAT_MODEL
    )
    response: AIAnswer = llm.ask('hello!')
    assert response is not None
    assert len(response.content) > 0
    assert isinstance(response, AIAnswer)
    # TODO: Return grounded tool info
