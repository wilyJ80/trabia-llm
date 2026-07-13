from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import ValidationError

from ai.models import AIAnswer


class LLM:
    def __init__(self, api_key: str, model: str) -> None:
        self.model: Runnable = ChatGoogleGenerativeAI(
            api_key=api_key, model=model
        ).with_structured_output(schema=AIAnswer)

    def ask(self, prompt: str) -> AIAnswer | None:
        try:
            response: AIAnswer = self.model.invoke(prompt)
            return response
        except ValidationError as e:
            print(f"LLM returned invalid data structure: {e}")
            return None  # Or handle your fallback logic here
