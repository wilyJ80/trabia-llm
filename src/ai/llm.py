from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from settings import Settings
from ai.models import AIAnswer

class LLM:
    def __init__(self, api_key: str, model: str) -> None:
        self.model: Runnable = ChatGoogleGenerativeAI(
            api_key=api_key, model=model
        ).with_structured_output(schema=AIAnswer)

    def ask(self, query: str) -> AIAnswer:
        response: AIAnswer = self.model.invoke(query)
        return response
