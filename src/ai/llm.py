from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from settings import Settings

class LLM:
    def __init__(self, api_key: str, model: str) -> None:
        self.model: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(
            api_key=api_key, model=model
        )

    def ask(self, query: str) -> str:
        response: AIMessage = self.model.invoke(query)
        return response.text
